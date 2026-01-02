from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Tuple
from .song_normalize import NormalizedSongInfo, normalize_title_and_artists, split_artists
from .genre_whitelist import GenreWhitelist, GenreTag

T = TypeVar('T')
A = TypeVar('A')

@dataclass
class TrackInfo:
  title: str
  artists: list[str]
  source_url: str

@dataclass
class BasicTrackInfo(TrackInfo,Generic[T]):
  raw_object:T

@dataclass
class TrackAndGenres:
  track:TrackInfo
  genres: list[GenreTag]
  canonicalized_genres: list[list[GenreTag]]

@dataclass
class ArtistInfo:
  artists: list[str]
  source_url: str

@dataclass
class BasicArtistInfo(ArtistInfo,Generic[A]):
  raw_object: A
  
@dataclass 
class ArtistAndGenres:
  artist:ArtistInfo
  genres: list[GenreTag]
  canonicalized_genres: list[list[GenreTag]]



PRINT_DEBUG=False

class BaseGenreSearch(ABC, Generic[T, A]):

  def __init__(self, title_cutoff=0.4, artist_cutoff=0.7):
    self.title_cutoff = title_cutoff
    self.artist_cutoff = artist_cutoff
    self.all_artists_weight = 1.0
    self.main_artist_weight = 0.5
    self.any_artist_weight = 0.25
    self.wh = GenreWhitelist()

  def fetch_artist_genres(self, artist: str):
    """Attempts to find the best matching artist and a list of genre tags for
    the given artist string
    """
    try:
      artist_info = self.fetch_artist(artist)
      if artist_info is None:
        return None
      genres = self._get_genre_tags_from_artist(artist_info)
      canonicalized_genres = self.wh.resolve_genres(genres)
      artist_and_genre = self._build_artist_and_genres(artist_info, genres, canonicalized_genres)
      return artist_and_genre
    except Exception as e:
      print(f"BaseGenreSearch.fetch_artist_genres: error fetching artist: {e}")
    return None
  
  def fetch_track_genres(self, artist: str, title: str, subtitle: str|None):
    """Attempts to find the best matching track and a list of genre tags for
    the given artist, title, and subtitle
    """
    try:
      track_matches = self._fetch_track_matches(artist, title, subtitle)
      if PRINT_DEBUG:
        print(f"Found {len(track_matches)} tracks")
        for t in track_matches:
          print(t[1])
          
      if len(track_matches) == 0:
        return None
      best_match = max(track_matches, key=lambda t: t[1])
      matching_track = best_match[0]
      match_threshold = best_match[1] * 0.95
      
      good_matches = [t for t in track_matches if t[1] >= match_threshold]

      # get the genres from the best matching tracks, and canonicalize the
      # whole set. This should hopefully give us a better consensus, with
      # more common tags ending up with a higher cumulative score
      genres: list[GenreTag] = []
      for match in good_matches:
        genres += self._get_genre_tags_from_track(match[0])
      
      canonicalized_genres = self.wh.resolve_genres(genres)
      

      track_and_genres = self._build_track_and_genres(matching_track, genres, canonicalized_genres)
      return track_and_genres
    except Exception as e:
      print(f"BaseGenreSearch.fetch_track_genres: error fetching track: {e}")
      print(e)
    
    return None

  def fetch_artist(self, artist: str):
    """Attempts to find the best matching artist for the given artist string"""
    artists = split_artists(artist)

    result_artists = self._do_several_fetch_artists(artists, artist)
    matching_artist = self.find_best_matching_artist(result_artists, artists)
    return matching_artist

  def fetch_track(self, artist:str, title: str, subtitle:str|None):
    """Attempts to find the best matching track for the given artist and title."""
    song_info = normalize_title_and_artists(artist, title, subtitle)
    if PRINT_DEBUG:
      print(song_info)
    result_tracks = self._do_several_fetch_tracks(song_info, artist, title, subtitle)
    matching_track = self.find_best_matching_track(result_tracks, song_info, artist, title, subtitle)
    if PRINT_DEBUG:
      print(matching_track)
    return matching_track
  

  def _fetch_track_matches(self, artist: str, title: str, subtitle:str|None):
    song_info = normalize_title_and_artists(artist, title, subtitle)
    if PRINT_DEBUG:
      print(song_info)
    result_tracks = self._do_several_fetch_tracks(song_info, artist, title, subtitle)
    tracks_and_scores = self.score_tracks(result_tracks, song_info, artist, title, subtitle)
    return tracks_and_scores
    

  def _do_several_fetch_artists(self, normalized_artists: list[str], artist: str):

    artists = self._perform_artist_search(normalized_artists)
    if len(normalized_artists) > 1 or normalized_artists[0] != artist:
      artists += self._perform_artist_search([artist])
    
    return artists

  
  def _do_several_fetch_tracks(self, normalized_song_info: NormalizedSongInfo, artist: str, title: str, subtitles:str|None):
    """Performs various searches for tracks using both normalized data
    and unnormalized data.
    """

    # first search with normalized track data
    tracks: list[BasicTrackInfo[T]] = []
    tracks = self._perform_track_search(normalized_song_info.artists, normalized_song_info.title, tracks)
    if normalized_song_info.subtitle is not None:
      normalized_full_title = f"{normalized_song_info.title} {normalized_song_info.subtitle}"
      tracks += self._perform_track_search(normalized_song_info.artists, normalized_full_title, tracks)
    
    # and now search for unnormalized data
    # (we should probably figure out some heuristic to decide whether
    # we got a good match from the normalized data)
    tracks += self._perform_track_search([artist], title, tracks)
    if subtitles is not None:
      full_title = f"{title} {subtitles}"
      tracks += self._perform_track_search([artist], full_title, tracks)
    
    return tracks


  
  def find_best_matching_track(self, tracks: list[BasicTrackInfo], song_info:NormalizedSongInfo, artist: str, title: str, subtitle:str|None):
    """Given a list of tracks, finds the track that best matches the given artist and title.
    """
    best_match = None
    best_similarity:float = 0
    for track in tracks:
      track_score = self.score_track(track, song_info, artist, title, subtitle)
      if track_score > best_similarity:
        best_match = track
        best_similarity = track_score
    
    return best_match
  
  def score_tracks(self, tracks: list[BasicTrackInfo], song_info: NormalizedSongInfo, artist: str, title: str, subtitle: str|None):
    tracks_and_scores:list[Tuple[BasicTrackInfo, float]] = []

    for track in tracks:
      track_score = self.score_track(track, song_info, artist, title, subtitle)
      tracks_and_scores.append((track, track_score))
    return tracks_and_scores

  def score_track(self, track: BasicTrackInfo, song_info: NormalizedSongInfo, artist: str, title: str, subtitle: str|None):
    title_sim = self.score_string(track.title, title)
    artist_sim = self._score_artist(track.artists, song_info.artists)
      
    if PRINT_DEBUG:
      print(f"track.title={track.title}, track.artists={track.artists}")
      print(f"title score={title_sim}")
      print(f"artist score={artist_sim}")
    
    if title_sim <= self.title_cutoff:
      title_sim = 0
    
    if artist_sim <= self.artist_cutoff:
      artist_sim = 0
    
    return artist_sim + title_sim
  
  def find_best_matching_artist(self, result_artists: list[BasicArtistInfo], searched_artists: list[str]):

    best_match = None
    best_similarity:float = 0

    for artist in result_artists:
      score = self._score_artist(artist.artists, searched_artists)
      if(score > self.artist_cutoff and score > best_similarity):
        best_match = artist
        best_similarity = score

    return best_match
  

  def _score_artist(self, result_artists: list[str], searched_artists: list[str]):

    sorted_result_artists = " ".join(sorted(result_artists))
    sorted_search_artists = " ".join(sorted(searched_artists))

    # compare both sets of all artists, it's unlikely that they'll all be a perfect match,
    # but a higher match here means that this is likely correct
    all_artists_score = self.score_string(sorted_result_artists, sorted_search_artists) * self.all_artists_weight
    # compare the first artist from both searched_artists and result_artists (which should be the "main" artist)
    main_artist_score = self.score_string(result_artists[0], searched_artists[0]) * self.main_artist_weight
    # and just in case the searched_artists and result_artists just disagree on which artist is the "main" artist,
    # check and see if there are any very good matches.
    any_artist_scores = [self.score_string(result_artists[0], a) for a in searched_artists]
    any_artist_scores = [s for s in any_artist_scores if s >= self.artist_cutoff * 0.9]
    any_artist_score = sum(any_artist_scores) * self.any_artist_weight

    total_score = all_artists_score + main_artist_score + any_artist_score

    if PRINT_DEBUG:
      print("===============")
      print(f"result_artists={result_artists}")
      print(f"searched_artists={searched_artists}")
      print(f"all_artists_score={all_artists_score}")
      print(f"main_artist_score={main_artist_score}")
      print(f"any_artist_score={any_artist_score}")
      print("===============")

    return total_score

  def get_best_matching_title(self, target_title: str, titles: list[str]):
    """Finds the title from the list of titles that
    best matches the target_title
    """
    best_match = None
    best_score = 0
    for t in titles:
      score = self.score_string(t, target_title)
      if score > best_score:
        best_match = t
        best_score = score
    
    return best_match

  def score_string(self, a:str, b:str):
    """Determines the similarity of two strings.
    Returns a value between 0.0 and 1.0, a higher value indicates
    more similarity.
    """
    r = SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
    return r
    
  def _build_track_and_genres(self, track:BasicTrackInfo, genres: list[GenreTag], canonicalized_genres: list[list[GenreTag]]):
    return TrackAndGenres(track=TrackInfo(title=track.title, artists=track.artists, source_url=track.source_url), genres=genres, canonicalized_genres=canonicalized_genres)
  
  def _build_artist_and_genres(self, artist_info: BasicArtistInfo, genres: list[GenreTag], canonicalized_genres: list[list[GenreTag]]):
    return ArtistAndGenres(artist=ArtistInfo(artists=artist_info.artists, source_url=artist_info.source_url), genres=genres, canonicalized_genres=canonicalized_genres)


  @abstractmethod
  def _perform_artist_search(self, artists: list[str]) -> list[BasicArtistInfo[A]]:
    pass

  @abstractmethod
  def _perform_track_search(self, artist:list[str], title:str, previous_tracks:list[BasicTrackInfo[T]]=[]) -> list[BasicTrackInfo[T]]:
    pass

  @abstractmethod
  def _get_genre_tags_from_artist(self, artist: BasicArtistInfo) -> list[GenreTag]:
    pass

  @abstractmethod
  def _get_genre_tags_from_track(self, track:BasicTrackInfo) -> list[GenreTag]:
    pass