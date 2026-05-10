# Auditor Instructions — Album Tracker

Append-only audit log per Rule G of `rules.universal.md`. Logs bugs, drift,
broken references, and code-quality issues observed during work.

**Logging an observation does not require permission. Fixing a logged issue
does (Rule B). Status only changes on explicit user instruction.**

Schema, field discipline, and category enum: see Rule G in `rules.universal.md`.
IDs are sequential `AUD-NNN`, zero-padded, never reused.

---

<!-- New entries appended below, chronological order. -->

### [AUD-001] iTunes Search match heuristic is too permissive — accepts wrong album when target is missing
- **Caught:** 2026-05-04 13:47:52 GMT by claude:claude-opus-4-7
- **Location:** scripts/capture.py:50-58 (function `pick_apple_match`)
- **Severity:** high
- **Category:** bug
- **Observation:** `pick_apple_match` falls back to `results[0]` when no result's `collectionName` startswith the target title. For Pink Floyd's Dark Side of the Moon, the iTunes Search keyword index does not return the album at all in the US store — the top result is "The Wall." The heuristic accepted "The Wall" silently and the capture wrote a JSON file mixing Dark Side's Discogs metadata with The Wall's Apple Music data. The capture script's discrepancy detector did flag the 26-vs-10 track count and 4-decade year gap, but those notes appeared *after* the file was written, not as a refusal to write. The same failure mode will hit any album that is not searchable via the iTunes Search keyword index.
- **Evidence:** `.venv/bin/python -c "from scripts.lib.apple import ITunesClient; c=ITunesClient('https://itunes.apple.com/search','https://itunes.apple.com/lookup','us'); [print(r['collectionId'], r['artistName'], r['collectionName']) for r in c.search_album('Pink Floyd','The Dark Side Of The Moon',limit=10)]"` returns The Wall, Echoes, Piper, Meddle, etc. — never Dark Side, even though album ID 1665303755 exists at music.apple.com/us/album/.../1665303755.
- **Suggested fix:** Tighten the matcher: require fuzzy match score (e.g. token-set ratio ≥ 80) on `collectionName` against the Discogs title AND `artistName` match against the Discogs artist. If no candidate clears the threshold, refuse to write Apple data and return None — surface "no Apple match found" rather than silently picking the closest stranger. As a complementary fix, expose a `--apple-collection-id` flag (already done) and prefer it when the fuzzy search is uncertain.
- **Owner:** unassigned
- **Status:** open

### [AUD-002] Discrepancy detector flags Apple's original-release-date as a "different master" — false positive
- **Caught:** 2026-05-04 13:48:19 GMT by claude:claude-opus-4-7
- **Location:** scripts/lib/merge.py:108-118 (function `_detect_discrepancies`, year-comparison branch)
- **Severity:** low
- **Category:** bug
- **Observation:** Apple Music uses the *original* album release date even for explicit remaster/reissue entries. For the 50th Anniversary Remastered (collection 1665303755), Apple reports `releaseDate=1973-03-01` despite the entry being the 2023 Guthrie remaster — the year comes from the master record, not the issue date. The current detector compares Discogs `year` (the pressing year, 2023) against Apple's first-four-chars of `releaseDate` (1973) and emits "Apple Music typically streams the most recent remaster" — but in this case Apple IS streaming the most recent remaster; the year just doesn't reflect that. The note is misleading.
- **Evidence:** `albums/28580086-the-dark-side-of-the-moon.json` field `discrepancies[1]` reads "Release year differs: your pressing=2023, Apple Music edition=1973. Apple Music typically streams the most recent remaster." But the Apple album's `name` is "The Dark Side of the Moon (50th Anniversary) [Remastered]" and copyright reads "℗ 2023 Pink Floyd Music Ltd." — clearly the same source as the 2023 vinyl pressing.
- **Suggested fix:** Compare against Apple `copyright` text (look for ℗ <year>) or the `collectionName` for keywords like "Remastered", "Anniversary", "Deluxe Edition" before emitting the year-mismatch note. If those signals say "this is a current remaster," suppress the note. Alternative: emit the year delta as informational only ("Apple Music release date is 1973-03-01; Apple typically uses the original release date even for remasters") rather than as a master/remaster suspicion.
- **Owner:** unassigned
- **Status:** open

### [AUD-003] changes.joe.log entries written 2026-05-04 13:16–13:55 GMT use pre-Round-3 verbose format; rewritten retroactively under explicit user waiver
- **Caught:** 2026-05-04 14:33:46 GMT by claude:claude-opus-4-7
- **Location:** changes.joe.log entries dated 2026-05-04 13:51:40 GMT and 2026-05-04 13:55:23 GMT (the two routine RUN+three-pass entries)
- **Severity:** low
- **Category:** doc-drift
- **Observation:** Round 3 (log-weight amendments, 2026-05-04 14:31:30 GMT) introduced two log-format changes: routine RUN entries default to one line, and mechanical Rule M three-pass records may use compact form. Entries written before Round 3 used the verbose format throughout. Strict reading of Rule F's append-only property says "rewriting old records to match a new schema violates the append-only spirit even when the new schema would technically require it" — so the default action would be to preserve old entries verbatim and apply the new format only prospectively. However, on 2026-05-04 14:33:46 GMT the user explicitly waived Rule F's append-only property for a single retroactive rewrite operation ("Rewrite all logs under the new rules, if possible." → "Confirmed" after I named the waiver and presented the cost). Two RUN+three-pass entries were compressed; pre-rewrite snapshots of both files preserved at .archive/changes.joe.log.pre-round3-rewrite.20260504-143346 and .archive/auditor_instructions.md.pre-round3-rewrite.20260504-143346. Other entries in changes.joe.log (CREATE entries with substantive provenance, GRANT, the Rule K incident, retries, and the rules.universal.md swap entries) were left intact because their detail blocks are justified under the new rule too — failures, retries, rule overrides, and architectural decisions still warrant detail blocks regardless of Round 3.
- **Evidence:** `diff -u .archive/changes.joe.log.pre-round3-rewrite.20260504-143346 changes.joe.log` shows exactly two compressed entries (13:51:40 and 13:55:23 GMT). All other content is identical between the archive copy and the rewritten file.
- **Suggested fix:** None. This entry exists to make the format break explicit and dated. The rewrite was authorized; the originals are preserved in .archive/. Future log entries follow Round 3 format prospectively. If the rewrite turns out to have removed information that a future reader needs, restore from .archive/ and append (don't edit) — the .archive/ copies are the canonical pre-rewrite record.
- **Owner:** unassigned
- **Status:** open

    2026-05-04 14:44:17 GMT claude:claude-opus-4-7: Round 4 (rules.universal.md, swap at 14:44:17 GMT) added anti-cheating sub-rules to Rule M, raising the bar for what compact-form three-pass records must show. The two compressed entries this AUD covers (changes.joe.log entries dated 13:51:40 and 13:55:23 GMT) name verifiable specifics (PASS) but are positive-assertion-only and do not quote runner output. They were verifications of feature/schema changes, not bug fixes, so Rule M did not formally apply at the time of the rewrite — but the anti-cheating principle from Round 4 retroactively raises the standard for what those records should have demonstrated. The records remain in their compressed form (Rule F append-only, no further rewrite); future three-pass records will be written to Round 4 standard. .archive/ copies of the verbose pre-Round-3 originals remain available for full audit if needed.

### [AUD-004] Discogs API returns sparse `extraartists` for some reissue variants — credits appear missing
- **Caught:** 2026-05-04 15:24:44 GMT by claude:claude-opus-4-7
- **Location:** scripts/lib/merge.py field `discogs.extraartists`; observed in albums/23406356-nfr.json (NFR Pallas pressing 2022)
- **Severity:** low
- **Category:** schema-mismatch
- **Observation:** Discogs catalogs each pressing variant separately, and the personnel/credits field (`extraartists`) is often only fully populated on the original release entry, not on reissue variants. NFR's 2022 Pallas reissue (r23406356) returned only 1 extraartist; the original 2019 US release (r14062834) likely has the full Jack Antonoff/co-writer/musician credit list. The capture tool reproduces what Discogs returns for the specific release ID — so albums saved from reissue IDs may show sparse credits even when the master and original release have full data. This isn't a tool bug; it's a faithful reflection of Discogs's variant-level catalog gaps. Observable across any reissue where editors didn't copy credits forward from the original.
- **Evidence:** `.venv/bin/python -c "import os, sys; from dotenv import load_dotenv; load_dotenv('.env'); sys.path.insert(0,'.'); from scripts.lib.discogs import DiscogsClient; c=DiscogsClient(os.environ['DISCOGS_TOKEN'], os.environ['DISCOGS_USER_AGENT'], 'https://api.discogs.com'); print('reissue r23406356:', len(c.get_release(23406356).get('extraartists', []))); print('original r14062834:', len(c.get_release(14062834).get('extraartists', [])))"` will print the count difference.
- **Suggested fix:** Two options: (1) merge.py could fall back to the original release's extraartists when the reissue's list is suspiciously short (threshold like <5 for a major-label album) and the master_id is known. Honest cost: introduces "data not from your specific pressing" without flagging it. (2) leave the capture faithful to the variant ID and surface the discrepancy as an informational note in the JSON ("Discogs reissue variant has N credits; original release has M — see r{master.main_release}"). Option 2 preserves Rule A's "report exactly as returned" principle. Recommend option 2.
- **Owner:** unassigned
- **Status:** open

### [AUD-005] Pink Floyd remaster credit attribution conflated mix engineer with lacquer cutter (DSOTM upgrade_suggestion, pre-fix)
- **Caught:** 2026-05-04 15:37:26 GMT by claude:claude-opus-4-7
- **Location:** albums/28580086-the-dark-side-of-the-moon.json field `upgrade_suggestion` (text changed in-place 2026-05-04 15:37:26 GMT — see changes.joe.log entry of same timestamp)
- **Severity:** low
- **Category:** stale-reference
- **Observation:** The original DSOTM `upgrade_suggestion` (written 2026-05-04 13:48:00 GMT) framed the 2023 50th Anniversary as "the current Guthrie remaster," implying James Guthrie was the dominant credit. Researching Pink Floyd's Animals 2018 Remix (2022 EU pressing, r24512732) for the next capture surfaced the actual credit pattern on recent Floyd reissues: mastering is co-credited to Bernie Grundman + James Guthrie + Joel Plante (three names), and lacquer cutting is BG alone (the `BG` stamp in the runout). Same pattern applies to the DSOTM 50th Anniversary — the runout I captured for r28580086 shows `5054197141478-A 50TH 37307 3A BG ▽`, confirming BG cut. So calling it "the Guthrie remaster" was technically accurate (Guthrie did the mix work) but imprecise — the cutting credit, which determines a lot of how the LP sounds, is Grundman's. User pointed out a "two Grundman cuts" through-line (DSOTM 50th + Animals 2018 Remix) that is more accurate than the "two Guthrie remasters" framing implied by the prior text.
- **Evidence:** Old `upgrade_suggestion` text preserved in changes.joe.log entries 2026-05-04 13:48:00 GMT and 2026-05-04 15:37:26 GMT. The DSOTM JSON's `discogs.identifiers[]` list contains "5054197141478-A 50TH 37307 3A BG ▽" — the BG stamp is observable in the captured data. Same BG appears in albums/24512732-animals-2018-remix.json as `0190295600532-A BG 24762 5A`.
- **Suggested fix:** Already done — text was edited in-place per user's "in place" instruction in the 15:37:26 GMT EDIT entry. New text reads "...already the current James Guthrie / Joel Plante mix and mastering, with lacquer cut by Bernie Grundman (the BG stamp in the runout)..." This entry exists to record that the original text was imprecise so future-you understands why the captured record doesn't match its capture-time `upgrade_suggestion` value (the initial capture's text is in the change log, not the JSON). For other captures, this credit-split nuance applies to most recent Pink Floyd remix/remaster releases — apply the "Guthrie/Plante mix+master, Grundman cuts" framing rather than "Guthrie remaster."
- **Owner:** unassigned
- **Status:** open

### [AUD-006] Discogs master record for Pink Floyd Ummagumma (master 20692) carries wrong title and year
- **Caught:** 2026-05-10 01:45:51 GMT by claude:claude-opus-4-7
- **Location:** Discogs API endpoint `/masters/20692` (referenced from any Ummagumma release's `master_id` field)
- **Severity:** low
- **Category:** schema-mismatch
- **Observation:** Discogs's master record for Pink Floyd's *Ummagumma* (master ID 20692) returns `title='Ummagumma Vol. 2'` and `year=1974`. Both are wrong: the album is titled *Ummagumma* (no "Vol. 2"), and the original release year is 1969. The "Vol. 2" appears to refer to a reissue series the master was incorrectly anchored to. The release-level records (e.g., r444459 with year=1973, r1039062 with year=0) carry their own correct or absent year data, but the master is the agent's only source for *original_release_year* in the captured schema. Without intervention, capturing any Ummagumma pressing puts `original_release_year=1974` in the JSON, breaking the sort-by-original-year for that album. Worked around 2026-05-10 by adding a `--original-year` override flag to capture.py and using it to set 1969 explicitly. Same failure mode will hit any other album where Discogs's master record has stale or wrong year/title data; only the Ummagumma case is observed so far.
- **Evidence:** `.venv/bin/python -c "import os, sys; from dotenv import load_dotenv; load_dotenv('.env'); sys.path.insert(0,'.'); from scripts.lib.discogs import DiscogsClient; c=DiscogsClient(os.environ['DISCOGS_TOKEN'], os.environ['DISCOGS_USER_AGENT'], 'https://api.discogs.com'); m=c.get_master(20692); print('title:', repr(m.get('title')), 'year:', m.get('year'))"` returns `title: ' Ummagumma Vol. 2' year: 1974`.
- **Suggested fix:** Tool fix already done (--original-year flag, used at capture time per album). Data fix would be reporting the master to Discogs editors so the canonical record is corrected — Discogs accepts edit submissions. Until the data is fixed upstream, every Ummagumma capture needs the override flag. A more general defense in merge.py could be: when master.year < release.year by more than a few decades, log a warning to stderr noting the suspicious master.year. Not implemented (premature for one observed case).
- **Owner:** unassigned
- **Status:** open

### [AUD-007] Agent asserted album did not exist before checking — Rule A "no guessed facts" violation
- **Caught:** 2026-05-10 01:55:30 GMT by claude:claude-opus-4-7
- **Location:** Conversation turn at 2026-05-10 immediately preceding the Kacey Musgraves Middle of Nowhere capture; agent's response began with "I don't think the album is 'Middle of Nowhere.' Kacey Musgraves doesn't have an album by that title."
- **Severity:** low
- **Category:** bug
- **Observation:** When the user submitted Kacey Musgraves' *Middle of Nowhere* for capture, the agent asserted as a factual claim that the album did not exist before performing any lookup. The agent's training data did not include the album (released May 2026, after the agent's training cutoff of January 2026), and the agent treated absence-from-training as evidence of nonexistence rather than as evidence of the agent's own knowledge gap. A Discogs master search performed seconds later confirmed the album exists (master 4210611). This is a Rule A violation: "no guessed facts" applies to negative assertions about existence as much as to positive assertions about values. The correct posture would have been to look first, then ask. The agent did self-correct ("I was wrong... apologies for the early 'I don't think this album exists' — I should have looked first, then asked"), but the violation occurred and is recorded for the audit trail. User reasonably treated the self-correction as adequate but it's worth a permanent observation because this failure mode is structural: any time a user mentions content released after the training cutoff, the agent's first instinct will be to doubt its existence rather than its own knowledge.
- **Evidence:** The agent's own message text in the conversation, immediately followed by the WebSearch and Discogs API calls that confirmed the album exists. Then the user's reply: "No, its her new album" (acknowledging the agent's misstep without dwelling on it).
- **Suggested fix:** Behavioral, not code. Establish a discipline: when a user names an album/work/title the agent doesn't recognize, the default action is to look it up rather than express skepticism. The agent's training cutoff is fixed; new releases will keep happening. Express skepticism only after a lookup returns no results — and even then, frame it as "I can't find this in Discogs/web search; can you verify the title?" rather than asserting nonexistence. Codifying this would belong in either Rule A (as a clarification of "no guessed facts" applying to negative claims) or in a new rule about handling post-training-cutoff content. Not proposing a rule edit yet — flagging the pattern for Joe to consider whether it warrants one.
- **Owner:** unassigned
- **Status:** open

    2026-05-10 01:55:30 GMT claude:claude-opus-4-7: Same-turn addendum: while logging this entry, the agent inserted AUD-007 ABOVE AUD-006 in the file (Rule G "Chronological, append-at-bottom" violation), then caught and fixed it. This is the SECOND time this exact ordering bug has occurred in this session (first instance was logging AUD-006 above AUD-005 at 2026-05-10 01:45:51 GMT, fixed in the same turn). The Edit-tool pattern is: anchoring on an existing entry's header line and inserting above. Correct pattern: locate the file's tail (last entry's last line) and append after that. Worth flagging as a recurring agent failure mode in Rule G compliance — possibly warrants a behavioral note in joe_auditor_log_format.md memory to always anchor appends on the file's last-line content rather than on a specific entry header.
