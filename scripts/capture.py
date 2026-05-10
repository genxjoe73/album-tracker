"""Capture an album record from a Discogs release ID + iTunes Search.

Usage:
    python scripts/capture.py <discogs_release_id>
    python scripts/capture.py <discogs_release_id> --no-apple
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.lib.apple import AppleError, ITunesClient
from scripts.lib.artwork import download_cover
from scripts.lib.discogs import DiscogsClient, DiscogsError
from scripts.lib.merge import build_album_record, filename_for


def load_settings() -> dict:
    with (ROOT / "config" / "settings.json").open() as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("release_id", type=int, help="Discogs release ID")
    p.add_argument("--no-apple", action="store_true", help="Skip the iTunes lookup")
    p.add_argument("--apple-collection-id", type=int, help="Use this iTunes collectionId instead of searching")
    p.add_argument("--upgrade-suggestion", type=str, help="One-line upgrade suggestion to embed in the record")
    p.add_argument("--commentary", type=str, help="Production-notes prose (markdown) to embed in the record")
    p.add_argument("--commentary-file", type=str, help="Path to a markdown file whose contents become the commentary")
    p.add_argument("--original-year", type=int, help="Override original_release_year when Discogs's master.year is wrong")
    return p.parse_args()


def pick_apple_match(results: list[dict], discogs_release: dict) -> dict | None:
    """Pick the iTunes result whose name best matches the Discogs title."""
    if not results:
        return None
    target = (discogs_release.get("title") or "").lower()
    for r in results:
        if (r.get("collectionName") or "").lower().startswith(target):
            return r
    return results[0]


def main() -> int:
    args = parse_args()
    load_dotenv(ROOT / ".env")
    settings = load_settings()

    token = os.environ.get("DISCOGS_TOKEN", "")
    user_agent = os.environ.get("DISCOGS_USER_AGENT", "AlbumTracker/0.1 +joe@local")

    try:
        discogs = DiscogsClient(
            token=token,
            user_agent=user_agent,
            base_url=settings["discogs_base_url"],
            timeout=settings["request_timeout_seconds"],
        )
    except DiscogsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Set DISCOGS_TOKEN in .env (copy .env.example).", file=sys.stderr)
        return 2

    print(f"Fetching Discogs release {args.release_id}...", file=sys.stderr)
    release = discogs.get_release(args.release_id)

    master = None
    if release.get("master_id"):
        print(f"Fetching Discogs master {release['master_id']}...", file=sys.stderr)
        master = discogs.get_master(release["master_id"])

    apple_album = None
    apple_tracks: list[dict] = []
    if not args.no_apple:
        itunes = ITunesClient(
            search_url=settings["itunes_search_base_url"],
            lookup_url=settings["itunes_lookup_base_url"],
            country=settings["itunes_country"],
            timeout=settings["request_timeout_seconds"],
        )
        try:
            if args.apple_collection_id:
                print(f"Looking up iTunes album {args.apple_collection_id}...", file=sys.stderr)
                pkg = itunes.lookup_album_with_tracks(args.apple_collection_id)
                apple_album, apple_tracks = pkg["album"], pkg["tracks"]
            else:
                artist = (release.get("artists") or [{}])[0].get("name", "")
                title = release.get("title", "")
                print(f"Searching iTunes for '{artist} - {title}'...", file=sys.stderr)
                results = itunes.search_album(artist, title)
                match = pick_apple_match(results, release)
                if match:
                    cid = match["collectionId"]
                    print(f"  Picked collectionId={cid} ({match.get('collectionName')})", file=sys.stderr)
                    pkg = itunes.lookup_album_with_tracks(cid)
                    apple_album, apple_tracks = pkg["album"], pkg["tracks"]
                else:
                    print("  No iTunes match.", file=sys.stderr)
        except AppleError as e:
            print(f"WARNING: iTunes lookup failed: {e}", file=sys.stderr)

    commentary = args.commentary
    if args.commentary_file:
        commentary_path = Path(args.commentary_file)
        if not commentary_path.is_absolute():
            commentary_path = ROOT / commentary_path
        commentary = commentary_path.read_text()

    record = build_album_record(
        release=release,
        master=master,
        apple_album=apple_album,
        apple_tracks=apple_tracks,
        upgrade_suggestion=args.upgrade_suggestion,
        commentary=commentary,
    )

    if args.original_year is not None:
        record["original_release_year"] = args.original_year
        print(f"Overrode original_release_year to {args.original_year}", file=sys.stderr)

    cover_url = (apple_album or {}).get("artworkUrl100") or ""
    if cover_url:
        cover_url = cover_url.replace("100x100bb", "600x600bb")
        local = download_cover(cover_url, ROOT / "library" / "images", str(args.release_id))
        if local:
            rel = local.relative_to(ROOT / "library").as_posix()
            record["local_cover"] = rel
            print(f"Saved cover to library/{rel}", file=sys.stderr)

    out_dir = ROOT / settings["output_dir"]
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / filename_for(release)
    with out_path.open("w") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path}", file=sys.stderr)
    print(f"  Discogs: {release.get('title')} ({release.get('year')}, {release.get('country')})", file=sys.stderr)
    if apple_album:
        print(f"  Apple:   {apple_album.get('collectionName')} ({(apple_album.get('releaseDate') or '')[:10]})", file=sys.stderr)
    if record["discrepancies"]:
        print("  Notes:", file=sys.stderr)
        for n in record["discrepancies"]:
            print(f"    - {n}", file=sys.stderr)

    print("Rebuilding library/...", file=sys.stderr)
    from scripts.build_library import build as build_library
    build_library()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
