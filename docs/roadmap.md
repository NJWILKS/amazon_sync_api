# Delivery roadmap

20 October2026. All implementation milestones are planned, not complete.

| Milestone | Deliverable | Exit criterion |
|---|---|---|
| M0 Requirements | Reviewed baseline, decisions and acceptance matrix | Confirm scope, priorities and unresolved live prerequisites |
| M1 Offline core | Source inventory, classification, state/plan model and provider test double | AT-01–09 and AT-17 synthetic cases pass; no credentials/network needed |
| M2 Container | Reproducible image, read-only source mounts, state/secrets boundaries and limits | Container/rebuild fixtures and secret checks pass |
| M3 Read-only provider | Reviewed/maintained Amazon adapter, correct UK endpoints, TLS and complete inventory | Private account pilot proves AT-04/06/12–14 without cloud writes |
| M4 Reconciliation | Existing-cloud matching and ambiguity/provenance report | User can assess coverage and a bounded upload plan |
| M5 Upload pilot | Upload-only execution and original download verification | Explicit small pilot passes conflict/restart/quota/retrieval cases |
| M6 Operations | State restore, independent content gaps, alerts and runbooks | AT-15/16 and recovery review pass |
| M7 Unattended release | Reviewed schedule and repeatable deployment | Evidence-backed go-live; no destructive behavior |

The operator's backup/recovery records remain authoritative for actual content protection. Creating this repository does not complete a backup or authorise production storage changes.
