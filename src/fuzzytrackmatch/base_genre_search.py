from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional

@dataclass
class GenreTag:
    name: str
    score: int

T = TypeVar('T')
@dataclass
class BasicTrackInfo(Generic[T]):
    title: str
    artist: str
    raw_object:Optional[T] = None
    


class BaseGenreSearch:

    def fetch_artist_genres(self, artist:str, match_thresh:float):
        pass

    def fetch_track_genres(self, artist:str, title:str, match_thresh:float):
        pass

    def _perform_track_search(self, artist:str, title:str) -> list[BasicTrackInfo]:
        pass

    def fetch_track(self, artist:str, title: str, match_thresh: float):
        """Attempts to find the best matching track for the given artist and title."""
        tracks = self._perform_track_search(artist, title)
        matching_track = self.find_best_matching_track(tracks, artist, title, match_thresh)
        return matching_track
    
    def find_best_matching_track(self, tracks: list[BasicTrackInfo], artist: str, title: str, match_thresh:float):
        """Given a list of tracks, finds the track that best matches the given artist and title.
        """
        best_match = None
        best_similarity:float = 0
        for track in tracks:
            title_sim = self.similarity(track.title, title)
            artist_sim = self.similarity(track.artist, artist)

            if title_sim > match_thresh and artist_sim > match_thresh and  title_sim + artist_sim > best_similarity:
                best_match = track
                best_similarity = title_sim + artist_sim
        
        return best_match

    def similarity(self, a:str, b:str):
        """Determines the similarity of two strings.
        Returns a value between 0.0 and 1.0, a higher value indicates
        more similarity.
        """
        r = SequenceMatcher(None, a.strip(), b.strip()).ratio()
        return r