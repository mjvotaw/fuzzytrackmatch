import time
from typing import Any, Dict, Optional

import requests

from .discogs_models import Release, Master, SearchResults


class DiscogsApiClient:
  def __init__(self, user_token: str, user_agent: str, base_url: str = "https://api.discogs.com", session: Optional[requests.Session] = None, max_retries: int = 3):
    if not user_token:
      raise ValueError("Discogs API token is required")
    if not user_agent:
      raise ValueError("User-Agent is required by Discogs API")

    self.token = user_token
    self.user_agent = user_agent
    self.base_url = base_url.rstrip("/")
    self.session = session or requests.Session()
    self.max_retries = max_retries

    # internal rate-limit tracking
    self.rate_limit: Optional[int] = None
    self.rate_limit_used: Optional[int] = None
    self.rate_limit_remaining: Optional[int] = None

    # set default headers on the session
    self.session.headers.update(self._default_headers())

  def _default_headers(self) -> Dict[str, str]:
    return {
      "User-Agent": self.user_agent,
      "Authorization": f"Discogs token={self.token}",
      "Accept": "application/vnd.discogs.v2+json",
    }

  def _update_rate_limit_from_response(self, resp: requests.Response) -> None:
    headers = resp.headers
    try:
      self.rate_limit = int(headers.get("X-Discogs-Ratelimit", self.rate_limit or 60))
    except Exception:
      pass
    try:
      self.rate_limit_used = int(headers.get("X-Discogs-Ratelimit-Used", self.rate_limit_used or 0))
    except Exception:
      pass
    try:
      self.rate_limit_remaining = int(headers.get("X-Discogs-Ratelimit-Remaining", self.rate_limit_remaining or 0))
    except Exception:
      pass

  def _full_url(self, path_or_url: str) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
      return path_or_url
    return f"{self.base_url}/{path_or_url.lstrip('/')}"

  def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = self._full_url(path)
    retries = 0
    while True:
      resp = self.session.request(method, url, params=params, json=json)
      self._update_rate_limit_from_response(resp)

      # Handle rate limiting: when remaining is 0 or explicit 429
      if resp.status_code == 429 or (self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0):
        # Prefer Retry-After header if present
        retry_after = None
        ra = resp.headers.get("Retry-After")
        try:
          if ra is not None:
            retry_after = int(ra)
        except Exception:
          retry_after = None
        wait = retry_after if retry_after is not None else 60
        time.sleep(wait)
        retries += 1
        if retries > self.max_retries:
          resp.raise_for_status()
        continue

      # Retry on 5xx with backoff
      if 500 <= resp.status_code < 600 and retries < self.max_retries:
        backoff = 2 ** retries
        time.sleep(backoff)
        retries += 1
        continue

      # For other status codes, raise for status (will raise HTTPError for 4xx/5xx)
      resp.raise_for_status()

      # Successful response
      if resp.status_code == 204:
        return {}
      return resp.json()

  def get_release(self, release_id: int) -> Release:
    """Fetch a release by id and return a `Release` dataclass."""
    data = self._request("GET", f"/releases/{int(release_id)}")
    return Release.from_dict(data)

  def get_master(self, master_id: int) -> Optional[Master]:
    data = self._request("GET", f"/masters/{int(master_id)}")
    return Master.from_dict(data)

  def search(
    self,
    query: Optional[str] = None,
    type_: Optional[str] = None,
    title: Optional[str] = None,
    release_title: Optional[str] = None,
    credit: Optional[str] = None,
    artist: Optional[str] = None,
    anv: Optional[str] = None,
    label: Optional[str] = None,
    genre: Optional[str] = None,
    style: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[str] = None,
    format_: Optional[str] = None,
    catno: Optional[str] = None,
    barcode: Optional[str] = None,
    track: Optional[str] = None,
    submitter: Optional[str] = None,
    contributor: Optional[str] = None,
    result_type: Optional[str] = None,
    per_page: Optional[int] = None,
    page: Optional[int] = None,
  ) -> SearchResults:
    """Search the Discogs database.

    Args:
      query: General search string.
      type_: One of 'release', 'master', 'artist', 'label'.
      title: Search by "Artist Name - Release Title" combined field.
      release_title: Search release titles.
      credit: Search release credits.
      artist: Search artist names.
      anv: Search artist ANV (Also Known As).
      label: Search label names.
      genre: Search genres.
      style: Search styles.
      country: Search release country.
      year: Search release year.
      format_: Search formats.
      catno: Search catalog number.
      barcode: Search barcodes.
      track: Search track titles.
      submitter: Search submitter username.
      contributor: Search contributor usernames.

    Returns:
      SearchResults: A paginated list of SearchResult objects with pagination info.
    """
    params = {}
    if query:
      params["q"] = query
    if type_:
      params["type"] = type_
    if title:
      params["title"] = title
    if release_title:
      params["release_title"] = release_title
    if credit:
      params["credit"] = credit
    if artist:
      params["artist"] = artist
    if anv:
      params["anv"] = anv
    if label:
      params["label"] = label
    if genre:
      params["genre"] = genre
    if style:
      params["style"] = style
    if country:
      params["country"] = country
    if year:
      params["year"] = year
    if format_:
      params["format"] = format_
    if catno:
      params["catno"] = catno
    if barcode:
      params["barcode"] = barcode
    if track:
      params["track"] = track
    if submitter:
      params["submitter"] = submitter
    if contributor:
      params["contributor"] = contributor
    if result_type:
      params["type"] = result_type
    if page:
      params["page"] = page
    if per_page:
      params["per_page"] = per_page
      
    data = self._request("GET", "/database/search", params=params)
    return SearchResults.from_dict(data)

  def raw_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generic GET that returns the parsed JSON dict."""
    return self._request("GET", path, params=params)


__all__ = ["DiscogsApiClient"]
