# Amazon Photos API capability evidence

Reviewed20 October2026. This is a source-evidence baseline, **not a claim of live compatibility**. No account/credentials or production content were used.

## What the evidence means

- **Implemented in inspected client:** pinned source constructs requests/parses responses for this operation. It is evidence of a reverse-engineered API shape, not an Amazon support guarantee or proof of current success.
- **Project documentation:** author describes behavior/limits; needs independent validation.
- **Live verified:** must name tested account region, version, scope and date. **No capability below is live verified by this project yet.**

Inspected sources:
- **S1:** [trevorhobenshield/amazon_photos API code, commit685c965](https://github.com/trevorhobenshield/amazon_photos/blob/685c965b5a4ba1ac85d418820ad200e12c18a46d/amazon_photos/_api.py).
- **S2:** [S1 constants](https://github.com/trevorhobenshield/amazon_photos/blob/685c965b5a4ba1ac85d418820ad200e12c18a46d/amazon_photos/_constants.py) and [metadata normalization](https://github.com/trevorhobenshield/amazon_photos/blob/685c965b5a4ba1ac85d418820ad200e12c18a46d/amazon_photos/_helpers.py).
- **S3:** [vanessa/immich-amazon-sync, commit6d95d8c](https://github.com/vanessa/immich-amazon-sync/blob/6d95d8cfed1f906606df24c7bc7d6b5eadee865d/src/immich_sync.py).
- **S4:** [standalone client README](https://github.com/trevorhobenshield/amazon_photos/blob/685c965b5a4ba1ac85d418820ad200e12c18a46d/README.md), which labels its search endpoints valid Dec2023 and its node documentation last updated2015. These are historical notes, not current official specifications.

## Read capabilities

| ID | Capability evidenced | Request/implementation evidence | Boundary / verification still needed |
|---|---|---|---|
| CAP-01 | Browser-session authentication | S1/S3 pass session-id and regional at/ubid cookies to internal web endpoints | No supported public OAuth/token-refresh contract established. Cookie lifetime, permissions and account isolation need tests |
| CAP-02 | Root/node lookup | S1 get_root, nodes, nodes_by_name; S3 get_root_id; GET /drive/v1/nodes with filters | Filter behavior and account ownership/access checks not live verified |
| CAP-03 | Photo/video search and filtering | S1 query/photos/videos use GET /drive/v1/search with filters, limit, offset and sort | Full pagination, large collections, stable snapshots and limits unverified |
| CAP-04 | File identifiers and metadata | S1/S2 consume node ID, name, size, content type, dates, dimensions, parents, ownerId and MD5 where supplied | Fields may be missing or differ by object/account. No universal metadata contract |
| CAP-05 | Usage reporting | S1 usage uses GET /drive/v1/account/usage; parses billable/total bytes and counts | Usage is not necessarily entitlement, remaining quota or upload eligibility. Exact quota discovery is still open |
| CAP-06 | Download by cloud node ID | S1 download calls GET /drive/v1/nodes/{id}/contentRedirection with download=true and streams the response | Must prove returned original bytes, redirects, filename safety and failure reporting; method returning node IDs alone is not recovery evidence |
| CAP-07 | Folder traversal | S1 get_folders calls GET /drive/v1/nodes/{id}/children with kind:FOLDER | Completeness/pagination and account-specific folder behavior need tests |
| CAP-08 | Aggregated metadata search | S1 aggregations uses /search and /search/aggregation for categories such as type, date, people/location/things | Potentially private metadata; unnecessary for first backup release. Correctness not verified |
| CAP-09 | Trash listing | S1 trashed calls GET /drive/v1/trash | Read capability exists in code; not needed for first backup release. Documented node/trash limits are not independently confirmed |

## Write capabilities visible in other clients

These are observed request implementations, **not proposed permission to execute them**.

| ID | Capability evidenced | Request/implementation evidence | Project scope |
|---|---|---|---|
| CAP-10 | Upload file content | S1 upload streams to regional content host /cdproxy/nodes; S3 uses multipart metadata/content to a North American endpoint | Required candidate capability; regional protocol, returned IDs, conflicts, formats and original preservation need a bounded pilot |
| CAP-11 | Create folders | S1 create_folders POSTs /drive/v1/nodes with kind:FOLDER and parents | Optional later feature; never during inventory/dry-run. Folder writes currently happen before its dedup check |
| CAP-12 | Create/rename albums and membership changes | S1 create_album uses kind:VISUAL_COLLECTION, then PATCH /nodes/{album}/children; rename_album/add_to_album/remove_from_album also implemented | Optional later; folders and albums are different objects. These methods do not constitute a tested complete album export API |
| CAP-13 | Trash and restore cloud items | S1 PATCH /drive/v1/trash; S3 PUT /drive/v1/trash/{node}; S1 restore removes trash membership | Intentionally excluded from backup worker; conflicting request styles reinforce need for current validation |
| CAP-14 | Permanent deletion | S1 delete POSTs /drive/v1/bulk/nodes/purge | Intentionally excluded; no delete API exposed by this project |
| CAP-15 | Favorites, hiding, family-vault/cluster edits | S1 has methods constructing settings/metadata mutations | Out of scope and unverified. Method presence is particularly weak evidence: favorite has a local argument-name mismatch, so source existence is not a working-feature test |

## Deduplication: capability versus policy

**CAP-16:** S1 exposes/consumes cloud MD5 metadata and compares local file MD5s against a cached inventory before upload. This is **client-side deduplication**, not proof of an atomic server-side deduplication API. S3 only tracks Immich asset IDs locally.

Neither codebase establishes:
- A guaranteed duplicate-free upload under lost acknowledgements or concurrent runs.
- A complete remote checksum inventory for every supported format.
- That an existing filename identifies the same original bytes.
- That metadata-edited copies have equal bytes or hashes.
- That HTTP409 means verified identical content.

Requirements INV-03–05 and UP-03–06 therefore cover reconciliation, idempotency and original-byte verification explicitly.

## Known implementation hazards, not API guarantees

- S1 asynchronous paths disable TLS verification; source cookie uk maps to www.amazon.uk rather than co.uk.
- S1 query fetches the initial offset again in its pagination loop. Its nodes/trash code/comments describe a first9999-node boundary; this is historical implementation evidence, not a current tested service limit.
- S1 fallback uploads without dedup if MD5 is absent; folder creation is performed before the dedup decision.
- S1 defaults to high concurrency and can return None after exhausted retries; refresh_db_aggressive is date-window/cache merging, not a demonstrated authoritative fresh inventory.
- S3 can trash previously tracked objects after one configured album disappears, and count an untracked conflict as upload success.
- Both clients use undocumented web endpoints. Current provider stability/compatibility is unproven.

No public supported Photos API contract was established by this review. An [Amazon Developer Community question from2024](https://community.amazondeveloper.com/t/restful-amazon-drive-api/5657) asks about the deprecated Drive API but receives a forum referral, not a replacement specification; do not treat that as official endpoint documentation.

## Requirements derived from evidence

| Requirement group | Evidence | Requirement consequence |
|---|---|---|
| INV-01–07 | CAP-02–08/16 | Private, complete source/cloud inventory with explicit missing-field/partial states and content/provenance reconciliation |
| UP-01–09 | CAP-06/10/16 | Bounded upload-only execution, durable intent/state, conflict reconciliation and downloaded-original verification |
| SAFE-01–06 | CAP-11–15 plus observed mirror behavior | No source writes/deletions or cloud destructive propagation; true no-write inventory/dry-run |
| SEC-01–06 | CAP-01/06/10 and TLS/region hazards | Verified TLS, region/redirect restrictions, private cookies and explicit expiry/account handling |
| OPS-01–08 | Client cache/concurrency/retry behavior | Independent persistent state, reproducible container, load limits and tested restart/recovery |

## First live questions to answer, read-only first

1. Which UK web/content endpoints and cookie names actually apply to the selected account?
2. Can a complete inventory be retrieved beyond the small-page/legacy node limits, with no duplicates/gaps?
3. Which objects expose comparable MD5, size and original-download access?
4. What do usage, entitlement and remaining capacity each mean for that account?
5. Do cookies expire/revoke cleanly without empty-library or false-success results?

Then a small upload/download pilot must establish original-byte preservation, formats, conflicts and repeated-run behavior. Those are test goals, not known capabilities today.

