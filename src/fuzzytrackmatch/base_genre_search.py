from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
from .song_normalize import NormalizedSongInfo, normalize_title_and_artists, split_artists
from .genre_whitelist import GenreWhitelist

@dataclass
class GenreTag:
  name: str
  score: float

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
  canonicalized_genres: list[list[str]]

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
  canonicalized_genres: list[list[str]]



PRINT_DEBUG=False

class BaseGenreSearch(ABC, Generic[T, A]):

  def __init__(self, title_cutoff=0.4, artist_cutoff=0.7):
    self.title_cutoff = title_cutoff
    self.artist_cutoff = artist_cutoff
    self.all_artists_weight = 1.0
    self.main_artist_weight = 0.5
    self.wh = GenreWhitelist()

  def fetch_artist_genres(self, artist: str):
    """Attempts to find the best matching artist and a list of genre tags for
    the given artist string
    """
    artist_info = self.fetch_artist(artist)
    if artist_info is None:
      return None
    genres = self._get_genre_tags_from_artist(artist_info)
    canonicalized_genres = self._canonicalize_genres(genres)
    artist_and_genre = self._build_artist_and_genres(artist_info, genres, canonicalized_genres)
    return artist_and_genre
  
  def fetch_track_genres(self, artist: str, title: str, subtitle: str|None):
    """Attempts to find the best matching track and a list of genre tags for
    the given artist, title, and subtitle
    """
    track = self.fetch_track(artist, title, subtitle)
    if track is None:
      return None
    
    genres = self._get_genre_tags_from_track(track)
    canonicalized_genres = self._canonicalize_genres(genres)
    track_and_genres = self._build_track_and_genres(track, genres, canonicalized_genres)
    return track_and_genres

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
    result_tracks = result_tracks
    matching_track = self.find_best_matching_track(result_tracks, song_info, artist, title, subtitle)
    if PRINT_DEBUG:
      print(matching_track)
    return matching_track
  

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

    tracks = self._perform_track_search(normalized_song_info.artists, normalized_song_info.title)
    if normalized_song_info.subtitle is not None:
      normalized_full_title = f"{normalized_song_info.title} {normalized_song_info.subtitle}"
      tracks += self._perform_track_search(normalized_song_info.artists, normalized_full_title)
    
    # and now search for unnormalized data
    # (we should probably figure out some heuristic to decide whether
    # we got a good match from the normalized data)
    tracks += self._perform_track_search([artist], title)
    if subtitles is not None:
      full_title = f"{title} {subtitles}"
      tracks += self._perform_track_search([artist], full_title)
    
    return tracks


  
  def find_best_matching_track(self, tracks: list[BasicTrackInfo], song_info:NormalizedSongInfo, artist: str, title: str, subtitle:str|None):
    """Given a list of tracks, finds the track that best matches the given artist and title.
    """
    best_match = None
    best_similarity:float = 0
    for track in tracks:
      title_sim = self.score_title(track.title, title)
      artist_sim = self._score_artist(track.artists, song_info.artists)
      
      if PRINT_DEBUG:
        print(f"track.title={track.title}, track.artists={track.artists}")
        print(f"title score={title_sim}")
        print(f"artist score={artist_sim}")

      if title_sim > self.title_cutoff and artist_sim > self.artist_cutoff and  title_sim + artist_sim > best_similarity:
        best_match = track
        best_similarity = title_sim + artist_sim
    
    return best_match
  
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

    all_artists_score = SequenceMatcher(None, sorted_result_artists, sorted_search_artists).ratio() * self.all_artists_weight

    main_artist_score = SequenceMatcher(None, result_artists[0], searched_artists[0]).ratio() * self.main_artist_weight

    if PRINT_DEBUG:
      print("===============")
      print(f"result_artists={result_artists}")
      print(f"searched_artists={searched_artists}")
      print(f"all_artists_score={all_artists_score}")
      print(f"main_artist_score={main_artist_score}")
      print("===============")
    
    return all_artists_score + main_artist_score

  def get_best_matching_title(self, target_title: str, titles: list[str]):
    """Finds the title from the list of titles that
    best matches the target_title
    """
    best_match = None
    best_score = 0
    for t in titles:
      score = self.score_title(t, target_title)
      if score > best_score:
        best_match = t
        best_score = score
    
    return best_match

  def score_title(self, a:str, b:str):
    """Determines the similarity of two strings.
    Returns a value between 0.0 and 1.0, a higher value indicates
    more similarity.
    """
    r = SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()
    return r
  
  def _canonicalize_genres(self, genres: list[GenreTag]) -> list[list[str]]:
    genre_names = [g.name for g in genres]
    return self.wh.resolve_genres(genre_names, 10)
  
  def _build_track_and_genres(self, track:BasicTrackInfo, genres: list[GenreTag], canonicalized_genres: list[list[str]]):
    return TrackAndGenres(track=TrackInfo(title=track.title, artists=track.artists, source_url=track.source_url), genres=genres, canonicalized_genres=canonicalized_genres)
  
  def _build_artist_and_genres(self, artist_info: BasicArtistInfo, genres: list[GenreTag], canonicalized_genres: list[list[str]]):
    return ArtistAndGenres(artist=ArtistInfo(artists=artist_info.artists, source_url=artist_info.source_url), genres=genres, canonicalized_genres=canonicalized_genres)


  @abstractmethod
  def _perform_artist_search(self, artists: list[str]) -> list[BasicArtistInfo[A]]:
    pass

  @abstractmethod
  def _perform_track_search(self, artist:list[str], title:str) -> list[BasicTrackInfo[T]]:
    pass

  @abstractmethod
  def _get_genre_tags_from_artist(self, artist: BasicArtistInfo) -> list[GenreTag]:
    pass

  @abstractmethod
  def _get_genre_tags_from_track(self, track:BasicTrackInfo) -> list[GenreTag]:
    pass