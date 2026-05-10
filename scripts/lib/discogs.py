"""Minimal Discogs API v2 client. Reads only — no writes."""
from __future__ import annotations

import time
from typing import Any

import requests


class DiscogsError(RuntimeError):
    pass


class DiscogsClient:
    def __init__(self, token: str, user_agent: str, base_url: str, timeout: int = 30):
        if not token:
            raise DiscogsError("DISCOGS_TOKEN is empty")
        if not user_agent:
            raise DiscogsError("DISCOGS_USER_AGENT is empty")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Authorization": f"Discogs token={token}",
            "Accept": "application/vnd.discogs.v2.discogs+json",
        })

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        remaining = resp.headers.get("X-Discogs-Ratelimit-Remaining")
        if remaining is not None and int(remaining) <= 1:
            time.sleep(1.1)
        if resp.status_code == 429:
            raise DiscogsError(f"Rate limited by Discogs at {url}")
        if resp.status_code != 200:
            raise DiscogsError(f"GET {url} returned {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def get_release(self, release_id: int, currency: str = "USD") -> dict[str, Any]:
        return self._get(f"/releases/{release_id}", params={"curr_abbr": currency})

    def get_master(self, master_id: int) -> dict[str, Any]:
        return self._get(f"/masters/{master_id}")

    def get_master_versions(self, master_id: int, per_page: int = 100) -> dict[str, Any]:
        return self._get(f"/masters/{master_id}/versions", params={"per_page": per_page})
