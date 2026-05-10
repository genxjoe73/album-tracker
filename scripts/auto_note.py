import json
import os
import sys
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    print("Please install google-generativeai: pip install google-generativeai")
    sys.exit(1)

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

def generate_note_for_album(json_path: Path):
    with json_path.open() as f:
        data = json.load(f)

    artist = data.get("artist", "Unknown Artist")
    title = data.get("title", "Unknown Title")
    year = data.get("original_release_year", data.get("year", ""))
    
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

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    print(f"Generating note for {artist} - {title}...")
    response = model.generate_content(prompt)
    
    slug = f"{title.lower().replace(' ', '-')}-{year}-gemini.md"
    # Keep alphanumeric and dashes only for slug
    slug = "".join(c for c in slug if c.isalnum() or c == '-')
    slug = slug.replace('--', '-')
    if not slug.endswith('-gemini.md'):
        slug = slug.replace('.md', '') + '-gemini.md'
    
    note_path = ROOT / "notes" / slug
    if note_path.exists():
        print(f"Gemini note already exists at {note_path.name}, skipping generation.")
        return note_path
        
    print(f"Generating note for {artist} - {title}...")
    response = model.generate_content(prompt)
    
    with note_path.open("w") as f:
        f.write(response.text)
    
    print(f"Saved note to {note_path.relative_to(ROOT)}")
    
    # Inject into JSON without overwriting existing (Claude's) notes
    existing = data.get("commentary", "")
    if existing:
        data["commentary"] = existing.strip() + f"\n\n### Gemini Notes\n\n{response.text}"
    else:
        data["commentary"] = response.text
        
    with json_path.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Injected commentary into {json_path.name}")
    
    # Rebuild HTML Library
    from build_library import build as build_library
    build_library()
    
    return note_path

if __name__ == "__main__":
    import time
    if len(sys.argv) > 1:
        # Process a specific file
        json_path = Path(sys.argv[1])
        if json_path.exists():
            generate_note_for_album(json_path)
    else:
        # Bulk process the albums directory
        print("Scanning library for albums missing Gemini notes...")
        albums_dir = ROOT / "albums"
        processed = 0
        for json_path in albums_dir.glob("*.json"):
            with json_path.open() as f:
                data = json.load(f)
            
            artist = data.get("artist", "Unknown Artist")
            title = data.get("title", "Unknown Title")
            year = data.get("original_release_year", data.get("year", ""))
            
            slug = f"{title.lower().replace(' ', '-')}-{year}-gemini.md"
            slug = "".join(c for c in slug if c.isalnum() or c == '-')
            slug = slug.replace('--', '-')
            if not slug.endswith('-gemini.md'):
                slug = slug.replace('.md', '') + '-gemini.md'
                
            note_path = ROOT / "notes" / slug
            
            # Skip if the Gemini note file already exists
            if note_path.exists():
                continue
            
            # Also skip if the existing commentary already has Gemini Notes header
            if "### Gemini Notes" in data.get("commentary", ""):
                continue
            
            generate_note_for_album(json_path)
            processed += 1
            time.sleep(2)  # brief pause to avoid hitting rate limits
            
        if processed == 0:
            print("All albums already have Gemini notes! Nothing to do.")
        else:
            print(f"Generated Gemini notes for {processed} albums.")
