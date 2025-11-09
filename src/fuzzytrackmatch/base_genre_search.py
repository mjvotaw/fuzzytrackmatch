from abc import ABC, abstractmethod
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
from .song_normalize import NormalizedSongInfo, normalize_title_and_artists, split_artists

@dataclass
class GenreTag:
    name: str
    score: int

T = TypeVar('T')

@dataclass
class BasicTrackInfo(Generic[T]):
    title: str
    artists: list[str]
    raw_object:T

@dataclass
class BasicArtistInfo(Generic[T]):
    artists: list[str]
    raw_object: T
    
@dataclass 
class ArtistAndGenres(Generic[T]):
    artist:BasicArtistInfo[T]
    genres: list[GenreTag]

@dataclass
class TrackAndGenres(Generic[T]):
    track:BasicTrackInfo[T]
    genres: list[GenreTag]

PRINT_DEBUG=False

class BaseGenreSearch(ABC):

    def __init__(self, title_cutoff=0.4, artist_cutoff=0.7):
        self.title_cutoff = title_cutoff
        self.artist_cutoff = artist_cutoff
        self.all_artists_weight = 1.0
        self.main_artist_weight = 0.5

    def fetch_artist_genres(self, artist: str):
        artist_info = self.fetch_artist(artist)
        if artist_info is None:
            return None
        genres = self._get_genre_tags_from_artist(artist_info)

        artist_and_genre = ArtistAndGenres(artist=artist_info, genres=genres)
        return artist_and_genre
    
    def fetch_track_genres(self, artist: str, title: str, subtitle: str=None):

        track = self.fetch_track(artist, title, subtitle)
        if track is None:
            return None
        
        genres = self._get_genre_tags_from_track(track)
        track_and_genres = TrackAndGenres(track=track, genres=genres)
        return track_and_genres

    def fetch_artist(self, artist: str):
        """Attempts to find the best matching artist for the given artist string"""
        artists = split_artists(artist)

        result_artists = self._perform_artist_search(artists, artist)
        matching_artist = self.find_best_matching_artist(result_artists, artists)
        return matching_artist

    def fetch_track(self, artist:str, title: str, subtitle:str=None):
        """Attempts to find the best matching track for the given artist and title."""
        song_info = normalize_title_and_artists(artist, title, subtitle)
        if PRINT_DEBUG:
            print(song_info)
        result_tracks = self._perform_track_search(song_info, artist, title, subtitle)
        result_tracks = result_tracks[:2]
        matching_track = self.find_best_matching_track(result_tracks, song_info, artist, title, subtitle)
        if PRINT_DEBUG:
            print(matching_track)
        return matching_track
    
    def find_best_matching_track(self, tracks: list[BasicTrackInfo], song_info:NormalizedSongInfo, artist: str, title: str, subtitle:str=None):
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


    def score_title(self, a:str, b:str):
        """Determines the similarity of two strings.
        Returns a value between 0.0 and 1.0, a higher value indicates
        more similarity.
        """
        r = SequenceMatcher(None, a.strip(), b.strip()).ratio()
        return r
    
    @abstractmethod
    def _perform_artist_search(self, normalized_artists: list[str], artist:str) -> list[BasicArtistInfo]:
        pass

    @abstractmethod
    def _perform_track_search(self, normalized_song_info: NormalizedSongInfo, artist:str, title:str, subtitle:str=None) -> list[BasicTrackInfo]:
        pass

    @abstractmethod
    def _get_genre_tags_from_artist(self, artist: BasicArtistInfo) -> list[GenreTag]:
        pass

    @abstractmethod
    def _get_genre_tags_from_track(self, track:BasicTrackInfo) -> list[GenreTag]:
        pass