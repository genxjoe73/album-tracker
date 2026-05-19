"""Combine a Discogs release + iTunes album into the canonical album JSON shape."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any


def _slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def _discogs_subset(release: dict[str, Any], master: dict[str, Any] | None) -> dict[str, Any]:
    """Pull only the fields we care about from a Discogs release + master."""
    artists = [
        {"name": a.get("name"), "id": a.get("id"), "role": a.get("role") or None}
        for a in release.get("artists", [])
    ]
    labels = [
        {"name": l.get("name"), "catno": l.get("catno"), "id": l.get("id")}
        for l in release.get("labels", [])
    ]
    formats = [
        {
            "name": f.get("name"),
            "qty": f.get("qty"),
            "descriptions": f.get("descriptions", []),
            "text": f.get("text"),
        }
        for f in release.get("formats", [])
    ]
    tracklist = [
        {
            "position": t.get("position"),
            "title": t.get("title"),
            "duration": t.get("duration"),
            "type": t.get("type_"),
        }
        for t in release.get("tracklist", [])
    ]
    extraartists = [
        {"name": e.get("name"), "role": e.get("role"), "id": e.get("id")}
        for e in release.get("extraartists", [])
    ]
    identifiers = [
        {"type": i.get("type"), "value": i.get("value"), "description": i.get("description")}
        for i in release.get("identifiers", [])
    ]
    images = [
        {"type": img.get("type"), "uri": img.get("uri"), "uri150": img.get("uri150")}
        for img in release.get("images", []) or []
    ]

    return {
        "release_id": release.get("id"),
        "master_id": release.get("master_id"),
        "uri": release.get("uri"),
        "title": release.get("title"),
        "artists": artists,
        "year": release.get("year"),
        "released": release.get("released"),
        "country": release.get("country"),
        "labels": labels,
        "formats": formats,
        "genres": release.get("genres", []),
        "styles": release.get("styles", []),
        "tracklist": tracklist,
        "extraartists": extraartists,
        "identifiers": identifiers,
        "notes": release.get("notes"),
        "images": images,
        "community": {
            "rating": (release.get("community") or {}).get("rating"),
            "have": (release.get("community") or {}).get("have"),
            "want": (release.get("community") or {}).get("want"),
        },
        "master": (
            {
                "id": master.get("id"),
                "title": master.get("title"),
                "main_release": master.get("main_release"),
                "year": master.get("year"),
                "uri": master.get("uri"),
                "num_for_sale": master.get("num_for_sale"),
            }
            if master
            else None
        ),
    }


def _apple_subset(album: dict[str, Any], tracks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": album.get("collectionId"),
        "url": album.get("collectionViewUrl"),
        "name": album.get("collectionName"),
        "artist": album.get("artistName"),
        "artist_id": album.get("artistId"),
        "artwork_url_100": album.get("artworkUrl100"),
        "artwork_url_600": (album.get("artworkUrl100") or "").replace("100x100bb", "600x600bb") or None,
        "release_date": album.get("releaseDate"),
        "track_count": album.get("trackCount"),
        "copyright": album.get("copyright"),
        "primary_genre": album.get("primaryGenreName"),
        "country": album.get("country"),
        "tracks": [
            {
                "track_number": t.get("trackNumber"),
                "disc_number": t.get("discNumber"),
                "name": t.get("trackName"),
                "duration_ms": t.get("trackTimeMillis"),
                "preview_url": t.get("previewUrl"),
                "track_view_url": t.get("trackViewUrl"),
            }
            for t in tracks
        ],
    }


def _duration_str_to_seconds(s: str | None) -> int | None:
    """Parse Discogs durations like '3:45' or '1:23:45'."""
    if not s:
        return None
    parts = s.split(":")
    try:
        nums = [int(p) for p in parts]
    except ValueError:
        return None
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


def _detect_discrepancies(
    discogs: dict[str, Any],
    apple: dict[str, Any] | None,
    main_release_id: int | None = None,
    main_release_credits_count: int | None = None,
) -> list[str]:
    notes: list[str] = []

    # AUD-006: master.year > release.year check
    master_info = discogs.get("master")
    if master_info:
        m_year = _year_or_none(master_info.get("year"))
        r_year = _year_or_none(discogs.get("year"))
        if m_year and r_year and m_year > r_year:
            import sys
            warning_msg = (
                f"WARNING: Discogs master year ({m_year}) is later than release year ({r_year}) "
                f"for master ID {master_info.get('id')}. The master year may be incorrect."
            )
            print(warning_msg, file=sys.stderr)
            notes.append(
                f"Discogs master year ({m_year}) is later than release year ({r_year}) — master data may be incorrect."
            )

    # AUD-004: sparse credits comparison
    if main_release_id is not None and main_release_credits_count is not None:
        current_credits_count = len(discogs.get("extraartists") or [])
        if current_credits_count < 5 and main_release_credits_count > current_credits_count:
            notes.append(
                f"Discogs reissue variant has sparse credits ({current_credits_count} credits); "
                f"original release (r{main_release_id}) has {main_release_credits_count} — some credits may be missing."
            )

    if not apple:
        notes.append("No Apple Music match found.")
        return notes

    d_tracks = discogs.get("tracklist") or []
    a_tracks = apple.get("tracks") or []
    d_count = len([t for t in d_tracks if (t.get("type") or "track") == "track"])
    a_count = len(a_tracks)
    if d_count != a_count:
        notes.append(f"Track count differs: Discogs={d_count}, Apple Music={a_count}")

    d_total = sum((_duration_str_to_seconds(t.get("duration")) or 0) for t in d_tracks)
    a_total = sum(int((t.get("duration_ms") or 0) / 1000) for t in a_tracks)
    if d_total and a_total and abs(d_total - a_total) > 30:
        notes.append(
            f"Total runtime differs by {abs(d_total - a_total)}s "
            f"(Discogs={d_total}s, Apple Music={a_total}s) — likely a different master/remaster."
        )

    # AUD-002: release year difference check with copyright/remaster suppression
    d_year = discogs.get("year")
    a_date = (apple.get("release_date") or "")[:4]
    if d_year and a_date and str(d_year) != a_date:
        copyright_str = apple.get("copyright") or ""
        c_years = re.findall(r"℗\s*(\d{4})", copyright_str)
        if not c_years:
            c_years = re.findall(r"\b(\d{4})\b", copyright_str)
        copyright_year = int(c_years[0]) if c_years else None

        coll_name = apple.get("name") or ""
        is_remaster = any(kw in coll_name for kw in ["Remaster", "Anniversary", "Deluxe", "Edition"])

        if copyright_year == d_year or is_remaster:
            pass
        else:
            notes.append(
                f"Release year differs: your pressing={d_year}, Apple Music edition={a_date}. "
                f"Apple Music typically streams the most recent remaster."
            )
    return notes


def _year_or_none(value: Any) -> int | None:
    """Discogs returns 0 for unknown year; normalize to None for clean sorting."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


def build_album_record(
    release: dict[str, Any],
    master: dict[str, Any] | None,
    apple_album: dict[str, Any] | None,
    apple_tracks: list[dict[str, Any]] | None,
    upgrade_suggestion: str | None = None,
    commentary: str | None = None,
    main_release_id: int | None = None,
    main_release_credits_count: int | None = None,
) -> dict[str, Any]:
    discogs = _discogs_subset(release, master)
    apple = _apple_subset(apple_album, apple_tracks or []) if apple_album else None
    artist_names = [re.sub(r"\s*\(\d+\)$", "", a["name"]) for a in discogs["artists"] if a.get("name")]
    artist_str = " / ".join(artist_names) if artist_names else None
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": 3,
        "artist": artist_str,
        "title": discogs.get("title"),
        "original_release_year": _year_or_none(master.get("year")) if master else None,
        "pressing_year": _year_or_none(release.get("year")),
        "upgrade_suggestion": upgrade_suggestion,
        "commentary": commentary,
        "discogs": discogs,
        "apple_music": apple,
        "discrepancies": _detect_discrepancies(
            discogs, apple, main_release_id=main_release_id, main_release_credits_count=main_release_credits_count
        ),
    }


def filename_for(release: dict[str, Any]) -> str:
    rid = release.get("id")
    title = release.get("title") or "untitled"
    return f"{rid}-{_slugify(title)}.json"
