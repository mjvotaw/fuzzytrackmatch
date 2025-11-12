from .discogs_api import DiscogsApiClient
from .discogs_models import Release, Artist, SearchResult
from .base_genre_search import BaseGenreSearch, GenreTag, BasicTrackInfo, BasicArtistInfo
from .song_normalize import NormalizedSongInfo


class DiscogsSearch(BaseGenreSearch[Release, Artist]):

    def __init__(self, api_key:str, title_cutoff=0.4, artist_cutoff=0.7):
        super().__init__(title_cutoff, artist_cutoff)
        self.discogs = DiscogsApiClient(user_agent='FuzzyTrackMatch/0.1', user_token=api_key)

    #region BaseGenreSearch methods

    def _perform_artist_search(self, artists: list[str]) -> list[BasicArtistInfo[Artist]]:
        return []
    

    def _perform_track_search(self, artists: list[str], title: str) -> list[BasicTrackInfo[Release]]:

        main_artist = artists[0]        
        results = self.discogs.search(track=title, artist=main_artist, result_type='release', per_page=10)
        p1_results: list[SearchResult] = results.results

        basic_tracks: list[BasicTrackInfo[Release]] = []
        for result in p1_results:
            if result.id:
                release = self.discogs.get_release(result.id)
                basic_track = self._discogs_release_to_basic_track(release, title)
                if basic_track is not None:
                    basic_tracks.append(basic_track)
        return basic_tracks

    def _get_genre_tags_from_track(self, track: BasicTrackInfo[Release]) -> list[GenreTag]:
        genre_tags = [GenreTag(name=g, score=0) for g in track.raw_object.genres]
        genre_tags += [GenreTag(name=s, score=0) for s in track.raw_object.styles]
        return genre_tags
    
    def _get_genre_tags_from_artist(self, artist: BasicArtistInfo) -> list[GenreTag]:
        return []
        
    #endregion


    def _discogs_release_to_basic_track(self, release: Release, normalized_title:str):
        artist_names: list[str] = [a.name for a in release.artists] # type: ignore
        track_titles: list[str] = [t.title for t in release.tracklist] # type: ignore
        best_matching_title = super().get_best_matching_title(normalized_title, track_titles)

        if best_matching_title is not None:
            basic_track = BasicTrackInfo(best_matching_title, artists=artist_names, source_url=str(release.url), raw_object=release)
            return basic_track

        else:
            return None
