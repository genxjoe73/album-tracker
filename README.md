# Album Tracker

A static album collection built from `albums/*.json`. The current library contains 100 albums, with generated detail pages, cover artwork, filtering, and sorting.

## Current host

**Live site:** https://album-tracker-production-4efd.up.railway.app/

Album Tracker is hosted on **Railway** using the `Procfile` static server (`python -m http.server 8000 --directory library --bind 0.0.0.0`).

| Setting | Value |
| --- | --- |
| Project ID | `ef2a08b0-83b6-453e-ae16-21276dc961ea` |
| Environment | `production` (`e8b241f8-d861-46c1-b438-7ead12a083ff`) |
| Service | `album-tracker` (`c4dff77a-8434-42b3-bead-71d12b15cbbf`) |
| GitHub repo | https://github.com/genxjoe73/album-tracker (`main`) |
| Latest verified deployment | `cf310666-54eb-48c5-a699-288114f721cf` (`SUCCESS`, commit `242c73c`) |
| Updates | Manual deploy via Railway CLI (`railway up`) |

Keep `.env` local and untracked (`DISCOGS_TOKEN`, `DISCOGS_USER_AGENT`, and `GEMINI_API_KEY` for optional note drafts). Hosting only serves the static `library/` directory and requires no secrets or database.

## Collection and scripts

- `albums/*.json`: one JSON record per owned edition (100 albums).
- `notes/`: production-notes markdown sources.
- `scripts/capture.py`: captures a Discogs release (optional Apple Music match, otherwise the Discogs primary cover) into `albums/` and `library/images/`, then rebuilds `library/`. Recapturing an existing album keeps its commentary, upgrade suggestion, and original release year unless those flags are passed.
- `scripts/build_library.py`: generates `library/index.html`, per-album detail pages (`library/<release_id>.html`), and `library/style.css`.
- `scripts/auto_note.py`: optional Gemini draft. Needs `GEMINI_API_KEY`. Writes `notes/<title>-<year>-gemini.md`, appends it to that album's commentary, and rebuilds `library/`.
- `library/`: committed publication output (101 HTML files, 100 cover images, 1 stylesheet).

## Update and deploy

1. Capture or update album records/notes locally.
2. Rebuild the static library if `build_library.py` was not already triggered by `capture.py`:

   ```sh
   .venv/bin/python scripts/build_library.py
   ```

   Inspect the generated JSON and rendered HTML (index row, cover reference, format, years, production notes, and upgrade note). With no album changes, the only diff is the “built” timestamp in `library/index.html`.
3. Review `git diff`, stage only intended files, commit, and push `main` to `origin` (with explicit approval).
4. Deploy to Railway using the Railway CLI:

   ```sh
   railway up --project ef2a08b0-83b6-453e-ae16-21276dc961ea --environment e8b241f8-d861-46c1-b438-7ead12a083ff --service c4dff77a-8434-42b3-bead-71d12b15cbbf --detach -m "Deploy Album Tracker"
   ```

5. Confirm the deployment reaches `SUCCESS`:

   ```sh
   railway deployment list --project ef2a08b0-83b6-453e-ae16-21276dc961ea --environment e8b241f8-d861-46c1-b438-7ead12a083ff --service c4dff77a-8434-42b3-bead-71d12b15cbbf --limit 3 --json
   ```

   Then verify https://album-tracker-production-4efd.up.railway.app/ serves the updated `index.html`, detail pages, and artwork.
