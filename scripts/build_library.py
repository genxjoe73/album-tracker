"""Build a static HTML library view from albums/*.json.

Outputs:
  library/index.html             — sortable, filterable table of all albums
  library/<release_id>.html      — per-album detail page
  library/style.css              — shared stylesheet

Usage:
  python scripts/build_library.py
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import markdown as _markdown

ROOT = Path(__file__).resolve().parent.parent
ALBUMS_DIR = ROOT / "albums"
LIBRARY_DIR = ROOT / "library"


def _esc(s: object) -> str:
    if s is None:
        return ""
    return html.escape(str(s))


def _wiki_slug(title: str) -> str:
    return title.replace(" ", "_")


def _format_summary(formats: list[dict]) -> str:
    parts = []
    for f in formats or []:
        bits = []
        qty = f.get("qty")
        if qty and qty != "1":
            bits.append(f"{qty}×")
        if f.get("name"):
            bits.append(f["name"])
        descs = f.get("descriptions") or []
        if descs:
            bits.append(", ".join(descs))
        if f.get("text"):
            bits.append(f"({f['text']})")
        parts.append(" ".join(bits))
    return " / ".join(parts)


def _label_summary(labels: list[dict]) -> str:
    seen = []
    for l in labels or []:
        name = l.get("name") or ""
        catno = l.get("catno") or ""
        key = f"{name} – {catno}" if catno else name
        if key and key not in seen:
            seen.append(key)
    return " / ".join(seen)


def _duration_str(ms_or_str) -> str:
    if isinstance(ms_or_str, int):
        s = ms_or_str // 1000
        return f"{s // 60}:{s % 60:02d}"
    return ms_or_str or ""


def _cover_url(record: dict) -> str | None:
    if record.get("local_cover"):
        return record["local_cover"]
    apple = record.get("apple_music") or {}
    if apple.get("artwork_url_600"):
        return apple["artwork_url_600"]
    if apple.get("artwork_url_100"):
        return apple["artwork_url_100"]
    return None


def _stylesheet() -> str:
    return """:root {
  color-scheme: light dark;
  --bg: #fafafa;
  --fg: #1a1a1a;
  --muted: #666;
  --border: #ddd;
  --accent: #0a66c2;
  --row-hover: #eef;
  --card: #fff;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14171a;
    --fg: #eaeaea;
    --muted: #999;
    --border: #2a2f33;
    --accent: #4ea1ff;
    --row-hover: #1c2126;
    --card: #1a1e22;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--fg); }
body { font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
header { padding: 18px 24px; border-bottom: 1px solid var(--border); display: flex; align-items: baseline; gap: 16px; }
header h1 { font-size: 18px; margin: 0; font-weight: 600; }
header .meta { color: var(--muted); font-size: 12px; }
main { padding: 16px 24px 64px; max-width: 1400px; margin: 0 auto; }

input.filter {
  width: 100%; padding: 10px 14px; font-size: 14px;
  border: 1px solid var(--border); border-radius: 6px;
  background: var(--card); color: var(--fg);
  margin-bottom: 16px;
}

table { border-collapse: collapse; width: 100%; }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: middle; }
th {
  position: sticky; top: 0; background: var(--bg);
  cursor: pointer; user-select: none; font-weight: 600;
  border-bottom: 2px solid var(--border);
}
th[aria-sort="ascending"]::after { content: " ▲"; color: var(--muted); }
th[aria-sort="descending"]::after { content: " ▼"; color: var(--muted); }
tr:hover td { background: var(--row-hover); }
td.cover { width: 64px; }
td.cover img { display: block; width: 56px; height: 56px; object-fit: cover; border-radius: 4px; background: var(--border); }
td.cover .placeholder { display: flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: var(--border); border-radius: 4px; color: var(--muted); font-size: 11px; }
td.year { text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Detail page */
.detail-grid { display: grid; grid-template-columns: 320px 1fr; gap: 32px; }
@media (max-width: 800px) { .detail-grid { grid-template-columns: 1fr; } }
.detail-cover img { width: 100%; max-width: 320px; border-radius: 6px; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }
.detail-cover .placeholder { width: 320px; height: 320px; display: flex; align-items: center; justify-content: center; background: var(--border); border-radius: 6px; color: var(--muted); }
.detail h1 { margin: 0 0 4px; font-size: 26px; }
.detail .artist { color: var(--muted); font-size: 18px; margin-bottom: 16px; }
.kv { display: grid; grid-template-columns: 160px 1fr; gap: 6px 18px; margin: 18px 0; }
.kv dt { color: var(--muted); }
.kv dd { margin: 0; }
.section { margin-top: 28px; }
.section h2 { font-size: 16px; margin: 0 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); font-weight: 600; }
.tracklist { width: 100%; border-collapse: collapse; }
.tracklist td { padding: 6px 8px; border-bottom: 1px solid var(--border); }
.tracklist td.pos { width: 50px; color: var(--muted); font-variant-numeric: tabular-nums; }
.tracklist td.dur { width: 70px; text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }
.credits, .identifiers { font-size: 13px; }
.credits li, .identifiers li { margin: 2px 0; }
.credits .role, .identifiers .type { color: var(--muted); }
.notes { white-space: pre-wrap; background: var(--card); padding: 12px; border-radius: 6px; border: 1px solid var(--border); font-size: 13px; }
.upgrade { background: var(--card); padding: 12px 14px; border-left: 3px solid var(--accent); border-radius: 4px; margin: 16px 0; font-size: 13px; }
.commentary { font-size: 14px; line-height: 1.55; }
.commentary p { margin: 0 0 12px; }
.commentary p:last-child { margin-bottom: 0; }
.commentary strong { color: var(--fg); }
.commentary em { color: var(--fg); }
.discrepancies { font-size: 13px; color: var(--muted); }
.discrepancies li { margin: 3px 0; }
.back { display: inline-block; margin-bottom: 16px; font-size: 13px; }
"""


def _index_script() -> str:
    return """
const tbody = document.querySelector('tbody');
const rows = Array.from(tbody.querySelectorAll('tr'));
const headers = document.querySelectorAll('th[data-sort]');

function getCell(row, key) {
  const td = row.querySelector(`td[data-${key}]`);
  return td ? td.dataset[key] : '';
}

let currentSort = { key: null, dir: 'asc' };

headers.forEach(h => {
  h.addEventListener('click', () => {
    const key = h.dataset.sort;
    const dir = (currentSort.key === key && currentSort.dir === 'asc') ? 'desc' : 'asc';
    currentSort = { key, dir };
    headers.forEach(x => x.removeAttribute('aria-sort'));
    h.setAttribute('aria-sort', dir === 'asc' ? 'ascending' : 'descending');
    const stripThe = s => s.replace(/^the[\\s]+/i, '');
    const sorted = rows.slice().sort((a, b) => {
      let va = getCell(a, key), vb = getCell(b, key);
      const na = parseFloat(va), nb = parseFloat(vb);
      if (!isNaN(na) && !isNaN(nb)) { va = na; vb = nb; }
      else {
        va = (key === 'artist' ? stripThe(va) : va).toLowerCase();
        vb = (key === 'artist' ? stripThe(vb) : vb).toLowerCase();
      }
      if (va < vb) return dir === 'asc' ? -1 : 1;
      if (va > vb) return dir === 'asc' ? 1 : -1;
      return 0;
    });
    sorted.forEach(r => tbody.appendChild(r));
  });
});

const filter = document.querySelector('input.filter');
filter.addEventListener('input', () => {
  const q = filter.value.toLowerCase().trim();
  rows.forEach(r => {
    const text = r.dataset.search || '';
    r.style.display = (!q || text.includes(q)) ? '' : 'none';
  });
});

// Default sort: artist asc, then original_release_year asc
document.querySelector('th[data-sort="artist"]').click();
"""


def _render_index(records: list[dict]) -> str:
    rows_html = []
    for rec in records:
        rid = (rec.get("discogs") or {}).get("release_id")
        artist = rec.get("artist") or ""
        title = rec.get("title") or ""
        oyear = rec.get("original_release_year")
        pyear = rec.get("pressing_year")
        d = rec.get("discogs") or {}
        fmt = _format_summary(d.get("formats") or [])
        country = d.get("country") or ""
        labels = _label_summary(d.get("labels") or [])
        cover = _cover_url(rec)
        cover_cell = (
            f'<img src="{_esc(cover)}" alt="" loading="lazy">'
            if cover
            else '<div class="placeholder">no art</div>'
        )
        search_blob = " ".join(
            str(x or "").lower() for x in (artist, title, oyear, pyear, fmt, country, labels)
        )
        rows_html.append(
            f"""<tr data-search="{_esc(search_blob)}">
  <td class="cover">{cover_cell}</td>
  <td data-artist="{_esc(artist)}"><a href="{rid}.html">{_esc(artist)}</a></td>
  <td data-title="{_esc(title)}"><a href="{rid}.html">{_esc(title)}</a></td>
  <td class="year" data-original_release_year="{_esc(oyear if oyear is not None else '')}">{_esc(oyear if oyear is not None else '')}</td>
  <td class="year" data-pressing_year="{_esc(pyear if pyear is not None else '')}">{_esc(pyear if pyear is not None else '')}</td>
  <td data-format="{_esc(fmt)}">{_esc(fmt)}</td>
  <td data-country="{_esc(country)}">{_esc(country)}</td>
  <td data-labels="{_esc(labels)}">{_esc(labels)}</td>
</tr>"""
        )
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M GMT")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Album Tracker — Library</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>Album Tracker</h1>
  <span class="meta">{len(records)} album{'s' if len(records) != 1 else ''} · built {_esc(built)}</span>
</header>
<main>
  <input class="filter" type="search" placeholder="Filter by artist, title, year, format, country, label…" autofocus>
  <table>
    <thead>
      <tr>
        <th></th>
        <th data-sort="artist">Artist</th>
        <th data-sort="title">Title</th>
        <th data-sort="original_release_year">Original</th>
        <th data-sort="pressing_year">Pressing</th>
        <th data-sort="format">Format</th>
        <th data-sort="country">Country</th>
        <th data-sort="labels">Label / Cat#</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows_html)}
    </tbody>
  </table>
</main>
<script>{_index_script()}</script>
</body>
</html>
"""


def _render_detail(record: dict) -> str:
    d = record.get("discogs") or {}
    a = record.get("apple_music") or {}
    rid = d.get("release_id")
    title = record.get("title") or "(untitled)"
    artist = record.get("artist") or ""
    cover = _cover_url(record)
    cover_block = (
        f'<img src="{_esc(cover)}" alt="cover">'
        if cover
        else '<div class="placeholder">no art</div>'
    )

    kv_rows = [
        ("Original release", record.get("original_release_year")),
        ("Pressing year", record.get("pressing_year")),
        ("Country", d.get("country")),
        ("Format", _format_summary(d.get("formats") or [])),
        ("Label / Cat#", _label_summary(d.get("labels") or [])),
        ("Genres", ", ".join(d.get("genres") or [])),
        ("Styles", ", ".join(d.get("styles") or [])),
        ("Discogs release", f'<a href="https://www.discogs.com/release/{rid}" target="_blank" rel="noopener">{rid}</a>' if rid else ""),
        ("Discogs master", f'<a href="https://www.discogs.com/master/{d["master"]["id"]}" target="_blank" rel="noopener">{d["master"]["id"]}</a>' if d.get("master") else ""),
        ("Apple Music", f'<a href="{_esc(a.get("url"))}" target="_blank" rel="noopener">{_esc(a.get("name"))}</a>' if a.get("url") else ""),
        ("Wikipedia", f'<a href="{_esc(record.get("wikipedia_url") or "https://en.wikipedia.org/wiki/" + _wiki_slug(title))}" target="_blank" rel="noopener">{_esc(title)}</a>'),
    ]
    kv_html = "\n".join(
        f"  <dt>{_esc(k)}</dt><dd>{v if v and ('<' in str(v)) else _esc(v)}</dd>"
        for k, v in kv_rows
        if v not in (None, "", [], {})
    )

    upgrade_html = (
        f'<div class="upgrade"><strong>Upgrade idea:</strong> {_esc(record.get("upgrade_suggestion"))}</div>'
        if record.get("upgrade_suggestion")
        else ""
    )

    commentary_html = ""
    commentary_text = record.get("commentary")
    if commentary_text:
        rendered = _markdown.markdown(commentary_text, extensions=["extra", "smarty"])
        commentary_html = f"""<div class="section">
  <h2>Production notes</h2>
  <div class="commentary">{rendered}</div>
</div>"""

    discrepancies_html = ""
    if record.get("discrepancies"):
        items = "\n".join(f"      <li>{_esc(x)}</li>" for x in record["discrepancies"])
        discrepancies_html = f"""<div class="section">
  <h2>Notes &amp; discrepancies</h2>
  <ul class="discrepancies">
{items}
  </ul>
</div>"""

    tracks = d.get("tracklist") or []
    tracks_html = ""
    if tracks:
        rows = "\n".join(
            f'      <tr><td class="pos">{_esc(t.get("position"))}</td><td>{_esc(t.get("title"))}</td><td class="dur">{_esc(t.get("duration"))}</td></tr>'
            for t in tracks
        )
        tracks_html = f"""<div class="section">
  <h2>Tracklist (Discogs)</h2>
  <table class="tracklist">
{rows}
  </table>
</div>"""

    apple_tracks = a.get("tracks") or []
    apple_tracks_html = ""
    if apple_tracks:
        rows = "\n".join(
            f'      <tr><td class="pos">{_esc(t.get("track_number"))}</td><td>{_esc(t.get("name"))}</td><td class="dur">{_esc(_duration_str(t.get("duration_ms")))}</td></tr>'
            for t in apple_tracks
        )
        apple_tracks_html = f"""<div class="section">
  <h2>Tracklist (Apple Music)</h2>
  <table class="tracklist">
{rows}
  </table>
</div>"""

    credits = d.get("extraartists") or []
    credits_html = ""
    if credits:
        items = "\n".join(
            f'      <li><strong>{_esc(c.get("name"))}</strong> <span class="role">— {_esc(c.get("role"))}</span></li>'
            for c in credits
        )
        credits_html = f"""<div class="section">
  <h2>Personnel &amp; credits</h2>
  <ul class="credits">
{items}
  </ul>
</div>"""

    identifiers = d.get("identifiers") or []
    ids_html = ""
    if identifiers:
        id_items = []
        for i in identifiers:
            desc = i.get("description")
            desc_html = f' <em>({_esc(desc)})</em>' if desc else ""
            id_items.append(
                f'      <li><span class="type">{_esc(i.get("type"))}:</span> '
                f'{_esc(i.get("value"))}{desc_html}</li>'
            )
        items = "\n".join(id_items)
        ids_html = f"""<div class="section">
  <h2>Identifiers</h2>
  <ul class="identifiers">
{items}
  </ul>
</div>"""

    notes = d.get("notes") or ""
    notes_html = f'<div class="section"><h2>Notes</h2><div class="notes">{_esc(notes)}</div></div>' if notes.strip() else ""

    captured = record.get("captured_at") or ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(artist)} — {_esc(title)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>Album Tracker</h1>
  <span class="meta">captured {_esc(captured)}</span>
</header>
<main class="detail">
  <a href="index.html" class="back">← back to library</a>
  <div class="detail-grid">
    <div class="detail-cover">{cover_block}</div>
    <div>
      <h1>{_esc(title)}</h1>
      <div class="artist">{_esc(artist)}</div>
      {upgrade_html}
      <dl class="kv">
{kv_html}
      </dl>
    </div>
  </div>
  {commentary_html}
  {tracks_html}
  {apple_tracks_html}
  {credits_html}
  {ids_html}
  {notes_html}
  {discrepancies_html}
</main>
</body>
</html>
"""


def build() -> int:
    LIBRARY_DIR.mkdir(exist_ok=True)
    records = []
    for path in sorted(ALBUMS_DIR.glob("*.json")):
        with path.open() as f:
            records.append(json.load(f))

    def _sort_artist(r):
        a = (r.get("artist") or "").lower()
        return re.sub(r"^the\s+", "", a)
    records.sort(key=lambda r: (_sort_artist(r), r.get("original_release_year") or 0))

    (LIBRARY_DIR / "style.css").write_text(_stylesheet())
    (LIBRARY_DIR / "index.html").write_text(_render_index(records))
    for rec in records:
        rid = (rec.get("discogs") or {}).get("release_id")
        if rid is None:
            continue
        (LIBRARY_DIR / f"{rid}.html").write_text(_render_detail(rec))

    print(f"Built library/ from {len(records)} album JSON files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
