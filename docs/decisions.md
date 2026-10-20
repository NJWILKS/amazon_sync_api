# Decisions and open questions

20 October2026. Requirements baseline v0.1 is draft; implementation choices below are not approved designs.

## Project scope established for this baseline

- Dedicated repository and requirements precede implementation.
- Standalone container deployment.
- Amazon Photos/Prime is the intended content provider.
- Existing cloud collections must be reconciled and preserved.
- Source storage and worker compute must be independently configurable.
- Private deployment names, addresses, account details and inventories remain outside this public repository.

## Proposed baseline to review

- Upload-only worker; source/cloud deletion excluded.
- Filesystem sources first, independent of Immich; optional future Immich adapter.
- Inventory and dry-run default; explicit bounded upload plans.
- Content/provenance ledger, private reconciliation and truthful verification levels.
- New project with a narrow provider adapter; upstream library versus maintained fork remains undecided.
- No unattended schedule or real account operation during requirements work.

## Open decisions

| ID | Question | Working assumption / release impact |
|---|---|---|
| D-01 | Exact source datasets and ownership? | Identify originals, managed storage, inbox/review, sidecars and owners separately. Do not assume every account user's assets are visible. |
| D-02 | Existing or new Amazon target account? | Preserve existing copies either way; bind plans/state to the chosen identity before live pilot. |
| D-03 | Actual account eligibility and capacity? | Verify quota and free/used split privately; no fixed allowance assumed. |
| D-04 | Match strategy for metadata-modified copies? | Whole-file hashes prove bytes, not visual equivalence. Provenance may aid review; never auto-delete either version. |
| D-05 | Verification sample/cadence policy? | Define coverage/size goals and full-retrieval policy before a recovery claim. |
| D-06 | Destination for videos, motion components, sidecars and documents? | Separate protection plan; Prime photo storage alone is insufficient. |
| D-07 | Provider library/fork/dependencies and licensing? | Review security, region and completeness issues; preserve notices. No upstream source imported yet. |
| D-08 | Scheduling, throughput and alerts? | Set an operational budget after fixture/pilot runs, accounting for other jobs. |
| D-09 | State/secret storage and refresh ownership? | Operator-configured private paths and documented independent recovery before deployment. |

SQLite schema, framework, CLI layout and scheduler are implementation choices, not requirements approvals.

## 20 October 2026 — collection model and prototype

Nick requested configurable collections: immich, captures and photoscans, each with its own source tree and Amazon root folder. Collection IDs and roots are independent of Amazon albums. A local experimental Python adapter and offline tests now exist; live compatibility and full requirements remain unverified. See [collections](collections.md). Docker files are proposed development scaffolding, not a tested deployment.


20 October 2026: user authorized manual GitHub smoke testing using the repository cookie secret and automatic account-root discovery, without separately configured account ID. This exception is limited to creating/reading one dedicated test folder; production account binding remains unchanged.
