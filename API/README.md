# Discogs API Documentation

Local copy of the Discogs API v2.0 reference, fetched from `https://www.discogs.com/developers/` (via the Internet Archive, since the live site is behind Cloudflare).

- **Base URL:** `https://api.discogs.com`
- **Version:** v2 (only supported version)
- **Default Accept header:** `application/vnd.discogs.v2.discogs+json`

## Sections

| File | Contents |
|---|---|
| [home.md](home.md) | Overview, quickstart, general info (User-Agent, rate limiting, pagination, errors, JSONP) |
| [authentication.md](authentication.md) | Discogs Auth (token / consumer key+secret) and OAuth 1.0a flow |
| [database.md](database.md) | Releases, Master Releases, Release Versions, Artists, Labels, Search |
| [images.md](images.md) | Image resource notes |
| [marketplace.md](marketplace.md) | Inventory, Listings, Orders, Order Messages, Fees, Price Suggestions, Release Stats |
| [inventory-export.md](inventory-export.md) | Export your marketplace inventory as CSV |
| [inventory-upload.md](inventory-upload.md) | Add/change/delete listings via CSV upload |
| [user-identity.md](user-identity.md) | Identity, Profile, Submissions, Contributions |
| [user-collection.md](user-collection.md) | Folders, Items, Custom Fields, Collection Value |
| [user-wantlist.md](user-wantlist.md) | Manage a user's wantlist |
| [user-lists.md](user-lists.md) | User-curated lists |

## Quick reference

Test request (no auth needed for public release data):

```http
curl https://api.discogs.com/releases/249504 --user-agent "MyApp/1.0"
```

### Notes
- Every request must send a unique `User-Agent` (see home.md).
- Rate limit: 60 requests/minute for authenticated, 25/min unauthenticated, returned via `X-Discogs-Ratelimit*` headers.
- Authenticated requests get access to image URLs and higher rate limits; some endpoints (collection, wantlist, marketplace write) require user authentication.
