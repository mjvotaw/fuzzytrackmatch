
import pylast
from .base_genre_search import BaseGenreSearch, GenreTag, BasicTrackInfo

PYLAST_EXCEPTIONS = (
    pylast.WSError,
    pylast.MalformedResponseError,
    pylast.NetworkError,
)

REPLACE = {
    "\u2010": "-",
}


class LastFMSearch(BaseGenreSearch):
    def __init__(self, api_key, min_weight=10):
        self.lastfm = pylast.LastFMNetwork(api_key=api_key)
        self.min_weight = min_weight

    def fetch_artist_genres(self, artist:str, match_thresh:float):
        """Returns the artist genres for this Item."""

        lastfm_artist = self.lastfm.get_artist(artist)
        if lastfm_artist is None:
            return []
        
        if self.similarity(artist, lastfm_artist.name) >= match_thresh:
            genres = self._fetch_genres(lastfm_artist)
            return genres
        return []

    def fetch_track_genres(self, artist:str, title:str, match_thresh:float):
        """Returns the track genres for this Item."""
        track_info:BasicTrackInfo[pylast.Track] = self.fetch_track(artist, title, match_thresh)
        if track_info != None:
            genres = self._fetch_genres(track_info.raw_object)
            return genres
        return []


    def _perform_track_search(self, artist, title):
        track_search = self.lastfm.search_for_track(artist_name=artist, track_name=title)
        tracks = track_search.get_next_page()
        track_infos = self._lastfm_to_basic_track(tracks)
        return track_infos

    def _lastfm_to_basic_track(self, tracks: list[pylast.Track]):
        track_infos = [BasicTrackInfo(title=track.title, artist=track.artist.name, raw_object=track) for track in tracks]
        return track_infos

    
    def _fetch_genres(self, lastfm_obj:pylast.Track):
        """Return the genre for a pylast entity or None if no suitable genre
        can be found. Ex. 'Electronic, House, Dance'
        """

        tags = self._tags_for(lastfm_obj, self.min_weight)
        return tags

    def _tags_for(self, obj, min_weight=None):
        """Core genre identification routine.

        Given a pylast entity (album or track), return a list of
        tag names for that entity. Return an empty list if the entity is
        not found or another error occurs.

        If `min_weight` is specified, tags are filtered by weight.
        """
        # Work around an inconsistency in pylast where
        # Album.get_top_tags() does not return TopItem instances.
        # https://github.com/pylast/pylast/issues/86
        if isinstance(obj, pylast.Album):
            obj = super(pylast.Album, obj)

        try:
            res = obj.get_top_tags()
        except PYLAST_EXCEPTIONS as exc:
            print(f"last.fm error: {exc}")
            return []
        except Exception as exc:
            # Isolate bugs in pylast.
            print(f"error in pylast library: {exc}")
            return []

        # Filter by weight (optionally).
        
        if min_weight:
            res = [el for el in res if (int(el.weight or 0)) >= min_weight]

        # Get strings from tags.

        res = [GenreTag(el.item.get_name().lower(), el.weight) for el in res]

        return res
