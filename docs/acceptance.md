# Acceptance scenarios

Version0.1,20 October2026. Proposed tests, **not executed**. Each scenario must record evidence, code/image version, fixture scope, outcome and unresolved items. Mocked success does not prove live Amazon behavior.

| Scenario | Requirements | Required evidence |
|---|---|---|
| AT-01 Read-only originals | SAFE-01, OPS-01 | Run against read-only synthetic mounts; source/sidecar hashes and paths unchanged after success/failure/restart. Attempted writes fail. |
| AT-02 No destructive propagation | SAFE-02, SAFE-05 | Remove/rename synthetic source selections and simulate missing/empty mounts/albums; no cloud trash/delete/move or metadata write is called. |
| AT-03 True dry-run | SAFE-03, UP-01 | Transport spies reject all write operations; inventory/dry-run works without folder creation/upload. |
| AT-04 Fail closed | SAFE-04, SEC-04 | Missing roots, permission failures, partial pages, corrupt state, missing MD5 and expired cookies produce failure/partial status and block bulk upload. |
| AT-05 Source boundaries | INV-01, INV-02, INV-07 | Nested sources, symlinks, loops, changing files, Unicode/duplicate basenames, inbox/review, videos/motion components, sidecars and derivatives are classified without escaping roots. |
| AT-06 Cloud completeness | INV-03 | Simulate large libraries/page limits, duplicate/missing pages, changing counts and retries. No incomplete inventory is marked complete. Validate actual provider behavior during read-only pilot. |
| AT-07 Existing-library reconciliation | INV-04, INV-05, UP-03 | Synthetic identical bytes under different names/IDs match; different bytes under same name do not. Metadata-modified historical copies are unresolved/versioned until justified. Verify representative real matches privately. |
| AT-08 Crash and lost acknowledgement | UP-04, OPS-03, OPS-05 | Interrupt before/during/after upload acknowledgment and checkpoint; resume reconciles unknown operations, retains evidence and prevents concurrent corruption. |
| AT-09 Conflict reporting | UP-05 | HTTP409 with/without node ID/checksum is not automatically counted as verified success. Error totals and statuses remain truthful. |
| AT-10 Original retrieval | UP-02, UP-06, UP-07 | Synthetic/pilot upload then download: size/SHA256 match. Inject preview/conversion/corruption and ensure verification fails. Clearly report sampled versus complete coverage. |
| AT-11 Capacity and unsupported media | UP-08, UP-09, INV-02 | Quota/eligibility changes, oversized video and unsupported sidecars stop or exclude visibly without silent gaps or source deletion. Inspect actual account allowance; no fixed allowance is pre-validated. |
| AT-12 TLS/region/redirects | SEC-01, SEC-02 | All network clients reject invalid certificates; UK maps to co.uk; malicious/unknown endpoint redirects cannot receive cookies. No permissive TLS settings. |
| AT-13 Secret/privacy handling | SEC-03, SEC-04, INV-06 | Cookie expiry/refresh, exceptions and retries reveal no secrets/private metadata to logs, images or Git. State/credentials have restricted access. |
| AT-14 Account isolation | SEC-05, SEC-06 | Different Amazon identities cannot share/apply state or plans accidentally; blocked operations remain blocked even through dependency helpers. |
| AT-15 Container/rebuild portability | OPS-01, OPS-02, OPS-04, OPS-07 | Rebuild from documented pins; validate mounts, user, limits, no ports/socket and streaming. Change only source mount configuration to exercise a simulated storage move. |
| AT-16 Recover state and operations | OPS-03, OPS-06, OPS-08 | Restore protected state into a fresh container; resume correctly, verify alert/staleness behavior and private completeness report. No unattended schedule before evidence review. |
| AT-17 Existing-copy preservation | SAFE-06, INV-04 | Old Amazon collection remains unchanged throughout read-only/pilot work; reconciliation report distinguishes verified, missing and unresolved objects. |

No production photo is a disposable test fixture. The first live pilot needs an explicitly selected scope; do not infer full-library upload permission from approval of these draft requirements.

## 20 October 2026 — implemented fixture integration test

`tests/test_live_amazon.py` adds opt-in real account connection, three configured roots, nested/empty folder checks, six synthetic PNG uploads, original retrieval/SHA-256 comparison and idempotent rerun. This partially exercises AT-01/03/08/11/14; it does not complete those scenarios. Offline fixture guard passed. Live test has not run: private credentials and expected account identity are not configured. See [execution instructions](integration-test.md).

