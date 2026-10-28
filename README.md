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

## Railway retired; service retained

Album Tracker’s Railway deployment was retired reversibly on 2026-10-28 after the Render replacement was verified.

| Retained Railway resource | ID |
| --- | --- |
| Project | `ef2a08b0-83b6-453e-ae16-21276dc961ea` |
| Production environment | `e8b241f8-d861-46c1-b438-7ead12a083ff` |
| Service | `c4dff77a-8434-42b3-bead-71d12b15cbbf` |
| Removed deployment | `5a82ee46-4c5a-4537-98ec-a2772d542024` |

Verification confirmed the deployment status is `REMOVED`, the active-deployment list is empty, and the service still exists. The project, service configuration, and Railway domain were retained; no service or project was permanently deleted.

The former URL is retained but currently serves HTTP 404 / “Application not found”:

https://album-tracker-production-4efd.up.railway.app/

It is not an active fallback or a redirect. Use the Render URL above. No custom-domain or DNS cutover was performed. Relay, Pawledger, and all other Railway services were untouched.

### Recover the Railway copy if needed

The existing `Procfile` and `.railway/` configuration are retained. Restoring runtime usage requires an explicitly approved new deployment to the retained service. Review the intended local source and generated library first, then run from this project directory:

```sh
railway up --project ef2a08b0-83b6-453e-ae16-21276dc961ea --environment e8b241f8-d861-46c1-b438-7ead12a083ff --service c4dff77a-8434-42b3-bead-71d12b15cbbf --detach -m "Restore Album Tracker Railway copy"
```

This starts a new deployment and resumes Railway runtime usage; it does not change the Render site. The detached command returning does not establish success. Inspect the scoped deployment until it reaches `SUCCESS`:

```sh
railway deployment list --project ef2a08b0-83b6-453e-ae16-21276dc961ea --environment e8b241f8-d861-46c1-b438-7ead12a083ff --service c4dff77a-8434-42b3-bead-71d12b15cbbf --limit 5 --json
```

Then verify the old URL’s expected collection count, detail pages, and artwork. Recovery has not been run as part of retirement.
