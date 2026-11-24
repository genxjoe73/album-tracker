"""Download album artwork into library/images/<release_id>.<ext> and return the local path.

Apple's CDN serves album art over plain HTTPS without auth. When Apple art is
unavailable, Discogs image URLs can be fetched by passing a User-Agent header.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import requests


def download_cover(
    url: str,
    dest_dir: Path,
    basename: str,
    timeout: int = 30,
    headers: dict[str, str] | None = None,
) -> Path | None:
    """Download `url` into `dest_dir/<basename>.<ext>`. Returns the local path or None.

    Skips download (and returns the existing path) if the destination file already exists.
    """
    if not url:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix or ".jpg"
    dest = dest_dir / f"{basename}{ext}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException:
        return None
    content_type = resp.headers.get("Content-Type", "")
    if (
        resp.status_code != 200
        or not resp.content
        or not content_type.startswith("image/")
    ):
        return None
    dest.write_bytes(resp.content)
    return dest
