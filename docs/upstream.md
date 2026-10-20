# Upstream evaluation

Source inspections were performed19 October2026. Findings require implementation tests and live read-only verification; no provider dependency is selected.

## Standalone candidate

- Repository: https://github.com/trevorhobenshield/amazon_photos
- Inspected commit:685c965b5a4ba1ac85d418820ad200e12c18a46d.
- MIT licence; retain notices if adopted.
- Provides usage, inventory, MD5 matching, streaming uploads and downloads.
- Source findings: asynchronous verify=False paths; UK cookie uk interpolated as amazon.uk rather than co.uk; folder writes before dedup; missing-MD5 fallback to upload all; pagination/completeness concerns, high default concurrency and weak failure reporting.
- Candidate transport/inventory code only; constructor performs live cloud reads/cache creation. Do not instantiate with real cookies during offline work.

## Immich-specific candidate

- Repository: https://github.com/vanessa/immich-amazon-sync
- Inspected commit:6d95d8cfed1f906606df24c7bc7d6b5eadee865d.
- MIT licence.
- Album mirror downloads originals and uploads to Amazon, but propagates removals to trash, has ID-only dedup, North American hard-coded content endpoint and fragile state.
- Offline characterization reproduced missing-album trash behavior, untracked409 success and filename traversal. Six upstream smoke tests plus three characterization tests passed by reproducing those behaviors; this is not a backup-safety pass.

## Provenance and project boundary

No upstream implementation is copied into this new requirements repository. It is not a GitHub fork and makes no claim to upstream endorsement. A fork, dependency or narrow replacement adapter is a later documented decision.
