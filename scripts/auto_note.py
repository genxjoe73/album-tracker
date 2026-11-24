import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from scripts.build_library import build as build_library


def note_slug(title: str, year: object) -> str:
    slug = f"{title.lower().replace(' ', '-')}-{year}-gemini.md"
    slug = "".join(c for c in slug if c.isalnum() or c in ("-", "."))
    while "--" in slug:
        slug = slug.replace("--", "-")
    if not slug.endswith("-gemini.md"):
        slug = slug.replace(".md", "") + "-gemini.md"
    return slug


def load_gemini():
    try:
        import google.generativeai as genai
    except ImportError:
        print("Please install google-generativeai: pip install google-generativeai")
        sys.exit(1)
    return genai


def generate_note_for_album(json_path: Path):
    with json_path.open() as f:
        data = json.load(f)

    artist = data.get("artist", "Unknown Artist")
    title = data.get("title", "Unknown Title")
    year = data.get("original_release_year", data.get("year", ""))

    note_path = ROOT / "notes" / note_slug(title, year)
    if note_path.exists():
        print(f"Gemini note already exists at {note_path.name}, skipping generation.")
        return note_path

    prompt = f"""
    Write a short, professional, and interesting album note (about 2-3 paragraphs) for the album "{title}" by {artist} (released in {year}).
    Include:
    1. Historical context about the album's recording or release.
    2. Its significance or interesting trivia.
    Format it as clean Markdown. Do not include a main title (no # header), just the text.
    """

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set in .env")
        sys.exit(1)

    genai = load_gemini()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"Generating note for {artist} - {title}...")
    response = model.generate_content(prompt)

    with note_path.open("w") as f:
        f.write(response.text)

    print(f"Saved note to {note_path.relative_to(ROOT)}")

    # Inject into JSON without overwriting existing (Claude's) notes
    existing = data.get("commentary", "")
    if existing:
        data["commentary"] = (
            existing.strip() + f"\n\n### Gemini Notes\n\n{response.text}"
        )
    else:
        data["commentary"] = response.text

    with json_path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Injected commentary into {json_path.name}")

    build_library()

    return note_path


def _pending_albums() -> list[Path]:
    pending = []
    for json_path in sorted((ROOT / "albums").glob("*.json")):
        with json_path.open() as f:
            data = json.load(f)
        title = data.get("title", "Unknown Title")
        year = data.get("original_release_year", data.get("year", ""))
        note_path = ROOT / "notes" / note_slug(title, year)
        if note_path.exists():
            continue
        if "### Gemini Notes" in data.get("commentary", ""):
            continue
        pending.append(json_path)
    return pending


if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
        if json_path.exists():
            generate_note_for_album(json_path)
    else:
        print(
            "Scanning albums for a missing <title>-<year>-gemini.md file. "
            "Each match appends a Gemini section onto the existing commentary."
        )
        pending = _pending_albums()
        if not pending:
            print("All albums already have Gemini notes! Nothing to do.")
        else:
            print(f"{len(pending)} albums are missing that note file.")
            for json_path in pending:
                generate_note_for_album(json_path)
                time.sleep(2)  # brief pause to avoid hitting rate limits
            print(f"Generated Gemini notes for {len(pending)} albums.")
