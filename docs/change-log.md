# Change log

## 20 October2026 — requirements baseline v0.1

Created dedicated project records: scope, stable requirement IDs, acceptance scenarios, decision log, upstream findings and staged roadmap. Requirements are draft for review. No app code, dependency selection, credentials, photo inventory, container deployment or live cloud operation. Production storage changes remain outside this requirements work.

Added a pinned-source API capability matrix: read/write operations, client-side MD5 versus server dedup distinction, historical documentation limits, known client defects, requirement mappings and read-only validation questions. No endpoint or account tested live.

## 20 October 2026 — local collection prototype

Implemented configurable collections, offline tree planning, account-bound SQLite checkpoints and an experimental upload/retrieval adapter. Added synthetic tests and CLI; three example collections have separate roots. No personal source modified, live Amazon request executed, service installed or recovery established. Docker scaffolding is untested. Remaining: transport testing, concurrent-run locking, opt-in synthetic live test, quota/eligibility validation and full recovery evidence. Retain state and remote objects on unknown outcomes; no deletion API provided.

## 20 October 2026 — opt-in real integration test

Added a real-provider synthetic tree test, private config template and execution/recovery instructions at Nick's request. Offline discovery: 19 tests, 17 passed, 2 skipped (live not enabled; Windows symlink privilege unavailable). Live fixture sources are generated independently of configured personal sources; test roots require an integration-test prefix. No Amazon connection made. Remaining prerequisite: private credentials and independently confirmed expected account ID; live API compatibility remains unverified. Retain test objects/checkpoints after failures.


## 20 October 2026 — manual GitHub smoke workflow
Added main-only workflow using AMAZON_PHOTOS_COOKIES, private temporary runner file and automatic root discovery. Creates/reuses and reads back one test folder; no uploads or deletion. Offline 20 passed, two skipped. Live execution pending. No recovery claim. Keep test folder after failures; inspect before retrying.

## 20 October 2026 — live GitHub connection/folder test passed
Run 39421837250 on commit 61b237609a40d16a73ed872b180f976296554ee4 passed at 12:23 UTC (13:23 BST). Authenticated root discovery and create/reuse of integration-test-amazon-sync-api followed by independent folder read-back succeeded. All 21 offline tests passed on Ubuntu; the opt-in full-tree test skipped. First run 39421583776 failed on non-JSON metadata; added JSON Accept header and full root-query parameters before the successful run. The individual cause is not isolated. No photos uploaded/deleted; full-tree upload, retrieval and recovery remain unverified. Secrets were masked and response bodies were not logged.

## 20 October 2026 — timestamped synthetic image smoke extension
Updated manual workflow to upload a valid generated 2x2 PNG under test/UTC-timestamp/, independently resolve the uploaded file, and stream/hash its original. Added mismatch/collision tests. Local 23 passed, two skipped; live run pending. No deletion API added. Keep failed test objects to diagnose unknown outcomes.
