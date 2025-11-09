
import pylast
from .base_genre_search import BaseGenreSearch, GenreTag, BasicTrackInfo, BasicArtistInfo
from .song_normalize import NormalizedSongInfo

PYLAST_EXCEPTIONS = (
    pylast.WSError,
    pylast.MalformedResponseError,
    pylast.NetworkError,
)

REPLACE = {
    "\u2010": "-",
}

PRINT_DEBUG=False

class LastFMSearch(BaseGenreSearch):
    def __init__(self, api_key, min_genre_weight=10, title_cutoff=0.4, artist_cutoff=0.7):
        super().__init__(title_cutoff, artist_cutoff)
        self.lastfm = pylast.LastFMNetwork(api_key=api_key)
        self.min_genre_weight = min_genre_weight

    #region BaseGenreSearch methods

    def _perform_track_search(self, normalized_song_info: NormalizedSongInfo, artist:str, title: str, subtitle:str=None):
        if PRINT_DEBUG:
            print(f"searching lastfm for artist='{artist}', title='{title}', subtitle='{subtitle}'")

        # lastfm only lists a single artist for songs, so only search for
        # the first artist in the given list
        main_artist = normalized_song_info.artists[0]
        normalized_title = normalized_song_info.title
        if normalized_song_info.subtitle is not None:
            normalized_title = f"{normalized_title} {normalized_song_info.subtitle}"

        track_search = self.lastfm.search_for_track(artist_name=main_artist, track_name=normalized_title)
        tracks = track_search.get_next_page()

        # And just in case, search for the unnormalized data as well
        unnormalized_title = title
        if subtitle is not None:
            unnormalized_title = f"{unnormalized_title} {subtitle}"
        unnormalized_search = self.lastfm.search_for_track(artist_name=artist, track_name=unnormalized_title)
        tracks.extend(unnormalized_search.get_next_page())
        if PRINT_DEBUG:
            print(f"found {len(tracks)} tracks")
        track_infos = self._lastfm_to_basic_track(tracks)
        return track_infos
    
    def _perform_artist_search(self, normalized_artists: list[str], artist: str):
        # lastfm only lists a single artist for songs, so only search for
        # the first artist in the given list
        artist_search = self.lastfm.search_for_artist(normalized_artists[0])

        # If the normalized artist info didn't return any results,
        # fall back to the unnormalized arist string
        if artist_search.get_total_result_count() == 0:
            artist_search = self.lastfm.search_for_artist(artist)
        
        normalized_artists = artist_search.get_next_page()
        artist_infos = self._lastfm_to_basic_artist(normalized_artists)
        return artist_infos

    def _get_genre_tags_from_artist(self, artist: BasicArtistInfo[pylast.Artist]):
        return self._fetch_genres(artist.raw_object)

    def _get_genre_tags_from_track(self, track: BasicTrackInfo[pylast.Track]):
        return self._fetch_genres(track.raw_object)
    #endregion

    #region other private methods
    def _lastfm_to_basic_artist(self, artists: list[pylast.Artist]):
        artist_infos = [BasicArtistInfo(artists=[a.name], source_url=a.get_url(), raw_object=a) for a in artists]
        return artist_infos

    def _lastfm_to_basic_track(self, tracks: list[pylast.Track]):
        track_infos = [BasicTrackInfo(title=track.title, artists=[track.artist.name], source_url=track.get_url(), raw_object=track) for track in tracks]
        return track_infos

    
    def _fetch_genres(self, lastfm_obj:pylast._Taggable):
        """Return the genre for a pylast entity or None if no suitable genre
        can be found. Ex. 'Electronic, House, Dance'
        """

        tags = self._tags_for(lastfm_obj, self.min_genre_weight)
        return tags

    def _tags_for(self, obj: pylast._Taggable, min_genre_weight=None):
        """Core genre identification routine.

        Given a pylast entity (album or track), return a list of
        tag names for that entity. Return an empty list if the entity is
        not found or another error occurs.

        If `min_genre_weight` is specified, tags are filtered by weight.
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
        
        if min_genre_weight:
            res = [el for el in res if (int(el.weight or 0)) >= min_genre_weight]

        # Get strings from tags.

        res = [GenreTag(el.item.get_name().lower(), el.weight) for el in res]

        return res

    #endregion
