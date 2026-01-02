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
  

  def _perform_track_search(self, artists: list[str], title: str, previous_tracks: list[BasicTrackInfo[Release]]=[]) -> list[BasicTrackInfo[Release]]:

    main_artist = artists[0]    
    results = self.discogs.search(track=title, artist=main_artist, result_type='release', per_page=10)
    p1_results: list[SearchResult] = results.results

    basic_tracks: list[BasicTrackInfo[Release]] = []
    for result in p1_results:
      if result.id:
        # don't re-retrieve this release if we've already grabbed it once before
        if any(prev_track.raw_object.id == result.id for prev_track in previous_tracks):
          continue
        # skip this release if it's not even close to what we're looking for
        if result.title is None or self._sanity_check_result_title(result.title, title, main_artist) == False:
          continue
        release = self.discogs.get_release(result.id)
        basic_track = self._discogs_release_to_basic_track(release, title)
        if basic_track is not None:
          basic_tracks.append(basic_track)
    return basic_tracks

  def _get_genre_tags_from_track(self, track: BasicTrackInfo[Release]) -> list[GenreTag]:
    genre_tags = [GenreTag(name=g, score=1) for g in track.raw_object.genres]
    genre_tags += [GenreTag(name=s, score=1) for s in track.raw_object.styles]
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

  def _sanity_check_result_title(self, result_artist_title: str, search_title: str, search_artist: str):
    """Sanity check that the title returned by the search results is even 
       slightly close to what we're looking for. If it's not, then we
       don't need to bother retrieving the full record from Discogs
    """
    if result_artist_title.count(" - ") == 1:
      result_parts = result_artist_title.split(" - ")
      result_artist = result_parts[0].strip()
      result_title = result_parts[1].strip()
      artist_score = self.score_string(result_artist, search_artist)
      title_score = self.score_string(result_title, search_title)
      return artist_score > 0.3 and title_score > 0.3
    else:
      search_artist_title = f"{search_artist} - {search_title}"

      score = self.score_string(search_artist_title, search_title)
      return score > 0.4
    