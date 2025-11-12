
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _maybe_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


@dataclass
class Artist:
    id: Optional[int]
    name: Optional[str]
    join: Optional[str] = None
    role: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Artist":
        if not d:
            return cls(id=None, name=None)
        return cls(
            id=_maybe_int(d.get("id")),
            name=d.get("name") or d.get("title"),
            join=d.get("join"),
            role=d.get("role"),
        )


@dataclass
class Track:
    position: Optional[str]
    title: Optional[str]
    duration: Optional[str] = None
    artists: List[Artist] = field(default_factory=list)
    credits: List[Artist] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Track":
        if not d:
            return cls(position=None, title=None)
        artists = [Artist.from_dict(x) for x in d.get("artists", []) if isinstance(x, dict)]
        credits = [Artist.from_dict(x) for x in d.get("extraartists", []) if isinstance(x, dict)]
        return cls(
            position=d.get("position"),
            title=d.get("title"),
            duration=d.get("duration"),
            artists=artists,
            credits=credits,
        )


@dataclass
class Video:
    title: Optional[str]
    uri: Optional[str]
    duration: Optional[str] = None
    embed: Optional[bool] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Video":
        if not d:
            return cls(title=None, uri=None)
        return cls(
            title=d.get("title"),
            uri=d.get("uri") or d.get("url"),
            duration=d.get("duration"),
            embed=d.get("embed"),
            description=d.get("description"),
        )


@dataclass
class Label:
    id: Optional[int]
    name: Optional[str]
    resource_url: Optional[str] = None
    catno: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Label":
        if not d:
            return cls(id=None, name=None)
        return cls(
            id=_maybe_int(d.get("id")),
            name=d.get("name"),
            resource_url=d.get("resource_url"),
            catno=d.get("catno") or d.get("catalogue_number"),
        )


@dataclass
class Price:
    value: Optional[float]
    currency: Optional[str]

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Price":
        if not d:
            return cls(value=None, currency=None)
        value = d.get("value")
        try:
            value = float(value) if value is not None else None
        except Exception:
            value = None
        return cls(value=value, currency=d.get("currency"))


@dataclass
class Rating:
    count: Optional[int]
    average: Optional[float]

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Rating":
        if not d:
            return cls(count=None, average=None)
        avg = None
        val = d.get("average")
        try:
            if val is not None:
                avg = float(val)
        except Exception:
            avg = None
        return cls(count=_maybe_int(d.get("count")), average=avg)


@dataclass
class User:
    id: Optional[int]
    username: Optional[str]
    resource_url: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "User":
        if not d:
            return cls(id=None, username=None)
        return cls(id=_maybe_int(d.get("id")), username=d.get("username"), resource_url=d.get("resource_url"))


@dataclass
class CommunityDetails:
    status: Optional[str]
    data_quality: Optional[str]
    want: Optional[int]
    have: Optional[int]
    rating: Optional[Rating] = None
    contributors: List[User] = field(default_factory=list)
    submitter: Optional[User] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["CommunityDetails"]:
        if not d:
            return None
        rating = Rating.from_dict(d.get("rating") or {})
        contributors = [User.from_dict(x) for x in d.get("contributors", []) if isinstance(x, dict)]
        submitter = User.from_dict(d.get("submitter")) if d.get("submitter") else None
        return cls(
            status=d.get("status"),
            data_quality=d.get("data_quality"),
            want=_maybe_int(d.get("want")),
            have=_maybe_int(d.get("have")),
            rating=rating,
            contributors=contributors,
            submitter=submitter,
        )


@dataclass
class Master:
    id: Optional[int]
    title: Optional[str]
    year: Optional[int] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> Optional["Master"]:
        if not d:
            return None
        return cls(id=_maybe_int(d.get("id")), title=d.get("title"), year=_maybe_int(d.get("year")))


@dataclass
class Release:
    id: Optional[int]
    title: Optional[str]
    year: Optional[int] = None
    thumb: Optional[str] = None
    data_quality: Optional[str] = None
    status: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    country: Optional[str] = None
    notes: Optional[str] = None
    formats: List[Dict[str, Any]] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    url: Optional[str] = None
    videos: List[Video] = field(default_factory=list)
    tracklist: List[Track] = field(default_factory=list)
    artists: List[Artist] = field(default_factory=list)
    artists_sort: Optional[str] = None
    credits: List[Artist] = field(default_factory=list)
    labels: List[Label] = field(default_factory=list)
    companies: List[Label] = field(default_factory=list)
    community: Optional[CommunityDetails] = None
    master: Optional[Master] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Release":
        # Basic scalars
        id_ = _maybe_int(d.get("id"))
        title = d.get("title")
        year = _maybe_int(d.get("year"))

        # Lists and nested objects
        videos = [Video.from_dict(v) for v in d.get("videos", []) if isinstance(v, dict)]
        tracklist = [Track.from_dict(t) for t in d.get("tracklist", []) if isinstance(t, dict)]
        artists = [Artist.from_dict(a) for a in d.get("artists", []) if isinstance(a, dict)]
        credits = [Artist.from_dict(a) for a in d.get("extraartists", []) if isinstance(a, dict)]
        labels = [Label.from_dict(l) for l in d.get("labels", []) if isinstance(l, dict)]
        companies = [Label.from_dict(l) for l in d.get("companies", []) if isinstance(l, dict)]

        community = CommunityDetails.from_dict(d.get("communitydetails")) if d.get("communitydetails") else None
        master = Master.from_dict({"id": d.get("master_id"), "title": None, "year": None}) if d.get("master_id") else None

        return cls(
            id=id_,
            title=title,
            year=year,
            thumb=d.get("thumb"),
            data_quality=d.get("data_quality"),
            status=d.get("status"),
            genres=list(d.get("genres") or []),
            images=list(d.get("images") or []),
            country=d.get("country"),
            notes=d.get("notes"),
            formats=list(d.get("formats") or []),
            styles=list(d.get("styles") or []),
            url=d.get("uri") or d.get("url"),
            videos=videos,
            tracklist=tracklist,
            artists=artists,
            artists_sort=d.get("artists_sort"),
            credits=credits,
            labels=labels,
            companies=companies,
            community=community,
            master=master,
        )


@dataclass
class SearchResult:
    """A lightweight result from a database search.
    
    These results have partial information; use the id and type to fetch
    the full object if needed (e.g., client.get_release(id)).
    """
    id: Optional[int]
    type: Optional[str]  # 'artist', 'release', 'master', 'label'
    title: Optional[str]
    resource_url: Optional[str] = None
    uri: Optional[str] = None
    thumb: Optional[str] = None
    year: Optional[int] = None
    country: Optional[str] = None
    format: Optional[List[str]] = None
    genre: Optional[List[str]] = None
    style: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "SearchResult":
        if not d:
            return cls(id=None, type=None, title=None)
        return cls(
            id=_maybe_int(d.get("id")),
            type=d.get("type"),
            title=d.get("title") or d.get("name"),
            resource_url=d.get("resource_url"),
            uri=d.get("uri"),
            thumb=d.get("thumb"),
            year=_maybe_int(d.get("year")),
            country=d.get("country"),
            format=list(d.get("format") or []) if isinstance(d.get("format"), list) else None,
            genre=list(d.get("genre") or []) if isinstance(d.get("genre"), list) else None,
            style=list(d.get("style") or []) if isinstance(d.get("style"), list) else None,
        )


@dataclass
class Pagination:
    """Pagination info from a paginated API response."""
    page: Optional[int] = None
    pages: Optional[int] = None
    per_page: Optional[int] = None
    items: Optional[int] = None
    urls: Optional[Dict[str, Optional[str]]] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Pagination":
        if not d:
            return cls()
        return cls(
            page=_maybe_int(d.get("page")),
            pages=_maybe_int(d.get("pages")),
            per_page=_maybe_int(d.get("per_page")),
            items=_maybe_int(d.get("items")),
            urls=d.get("urls"),
        )


@dataclass
class SearchResults:
    """Search results with pagination info."""
    results: List[SearchResult] = field(default_factory=list)
    pagination: Optional[Pagination] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "SearchResults":
        if not d:
            return cls()
        results = [SearchResult.from_dict(r) for r in d.get("results", []) if isinstance(r, dict)]
        pagination = Pagination.from_dict(d.get("pagination"))
        return cls(results=results, pagination=pagination)


__all__ = [
    "Artist",
    "Track",
    "Video",
    "Label",
    "Price",
    "Rating",
    "User",
    "CommunityDetails",
    "Master",
    "Release",
    "SearchResult",
    "Pagination",
    "SearchResults",
]
