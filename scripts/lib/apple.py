"""iTunes Search API client. No auth required.

Docs: https://performance-partners.apple.com/search-api
"""
from __future__ import annotations

from typing import Any

import requests


class AppleError(RuntimeError):
    pass


class ITunesClient:
    def __init__(self, search_url: str, lookup_url: str, country: str = "us", timeout: int = 30):
        self.search_url = search_url
        self.lookup_url = lookup_url
        self.country = country
        self.timeout = timeout
        self.session = requests.Session()

    def search_album(self, artist: str, title: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search for albums matching artist+title. Returns list of album dicts."""
        params = {
            "term": f"{artist} {title}",
            "media": "music",
            "entity": "album",
            "country": self.country,
            "limit": limit,
        }
        resp = self.session.get(self.search_url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            raise AppleError(f"iTunes search returned {resp.status_code}: {resp.text[:300]}")
        return resp.json().get("results", [])

    def lookup_album_with_tracks(self, collection_id: int) -> dict[str, Any]:
        """Look up an album by collectionId and return album + its tracks.

        Returns: {"album": {...}, "tracks": [...]}
        """
        params = {
            "id": collection_id,
            "entity": "song",
            "country": self.country,
        }
        resp = self.session.get(self.lookup_url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            raise AppleError(f"iTunes lookup returned {resp.status_code}: {resp.text[:300]}")
        results = resp.json().get("results", [])
        album = next((r for r in results if r.get("wrapperType") == "collection"), None)
        tracks = [r for r in results if r.get("wrapperType") == "track"]
        if album is None:
            raise AppleError(f"No album found for collectionId={collection_id}")
        tracks.sort(key=lambda t: (t.get("discNumber", 1), t.get("trackNumber", 0)))
        return {"album": album, "tracks": tracks}
