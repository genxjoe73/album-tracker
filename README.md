# Album Tracker

A static album collection built from `albums/*.json`. The current library contains 100 albums, with generated detail pages, cover artwork, filtering, and sorting.

## Current host

**Live site:** https://album-tracker-69c5.onrender.com/

Album Tracker runs as a Render Static Site in Joseph’s workspace. Hosting was verified on 2026-10-28. Static hosting has a free base price; outbound bandwidth and build pipeline usage count against workspace allowances.

| Setting | Value |
| --- | --- |
| Service | `album-tracker` |
| Render service ID | `srv-dbglkpnb9u1s738lqr6g` |
| Dashboard | https://dashboard.render.com/static/srv-dbglkpnb9u1s738lqr6g |
| Source | https://github.com/genxjoe73/album-tracker |
| Branch | `main` |
| Repository connection | Public Git repository URL; no Git provider integration |
| Root directory | Repository root (blank in the Dashboard) |
| Build command | `test -f library/index.html` |
| Publish directory | `library` |
| Environment | `SKIP_INSTALL_DEPS=true` |
| Updates | Manual deploy from the Render Dashboard |

Render publishes the committed `library/` files directly. Hosting requires no application secrets, persistent disk, or database. Local collection tools can use provider credentials; keep `.env` local and untracked. Do not copy it to Render for static hosting.

## Collection and generated files

- `albums/*.json`: collection records used by the generator.
- `notes/`: source notes for local collection work.
- `scripts/build_library.py`: generates the index, album detail pages, and stylesheet.
- `library/`: committed publication output: 101 HTML files, 100 JPEG covers, and one stylesheet at the verified 100-album baseline.

The Relay chat widget was removed from both the generated index and its template in commit `4cdc48c81054184b151f26644aded22f5265fa07`. Future rebuilds keep it removed.

## Update and deploy

Follow `rules.universal.md` for change approval, verification, and logging. Review existing local changes before staging anything.

1. Update the intended collection records, notes, or generator locally.
2. If content changed, rebuild with the existing project environment:

   ```sh
   .venv/bin/python scripts/build_library.py
   ```

   This writes generated files under `library/`. Review the output and confirm the expected album count, detail links, and covers. The Render build command only checks that the committed index exists; it does not regenerate the collection.

3. Review the exact diff, stage only intended files, and commit. Obtain the required approval before publishing to `main`, then run `git push origin main`.
4. Open the Render Dashboard above. Choose **Manual Deploy → Deploy latest commit**. A GitHub push alone does not trigger deployment with the current public-repository connection.
5. Confirm the deployment is **Live** and its source SHA matches the intended commit. Open the live site and verify the album count, filtering, sorting, detail pages, and artwork.
6. Record the observed outcome in `changes.joe.log`.

The latest verified application deployment is `dep-dbglp4vlk1mc738t9o6g`, using commit `4cdc48c81054184b151f26644aded22f5265fa07`. All 202 publication files were verified; the live index matches the widget-free committed file. Cloudflare may optimize JPEG responses, so image bytes can differ while the originals remain unchanged in Git.

## Railway fallback

The former Railway URL remains available as a fallback:

https://album-tracker-production-4efd.up.railway.app/

Railway has not been retired or changed as part of this pilot. Its retained deployment is the earlier 100-album version, before the widget removal. The existing `Procfile` and `.railway/` configuration are retained for that fallback; use the Render workflow above for updates to the current live site.

No custom domain or DNS cutover was performed. The user has authorized reversible retirement of only Album Tracker on Railway after Render verification. Retirement is pending confirmation; the coordinating task will perform and verify it separately. Do not treat this README as evidence that Railway has already been stopped, and do not permanently delete the service. Relay and Pawledger are separate applications and were not changed by this migration.
