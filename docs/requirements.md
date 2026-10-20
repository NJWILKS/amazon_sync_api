# Requirements

Version0.1,20 October2026. **Draft for review**; a requirement below is a proposed baseline, not proof that a feature exists. No implementation is authorised merely by marking a milestone planned.

Read [API capability evidence](api-capabilities.md) first. Existing client implementations are evidence for candidate operations, not a current provider guarantee. No live operation is verified yet.

## Problem and outcome

Operators may have curated filesystem photos, application-managed originals and a pre-existing Amazon Photos collection. The product must provide durable off-site photo coverage without uploading everything blindly, propagating deletions or confusing an upload attempt with a verified copy.

Amazon Photos is a content destination. It does not replace Nextcloud/Immich configuration/database backups or independently cover videos, documents and sidecars.

## Context and scope

- Standalone container deployment on an operator-controlled host.
- Source storage can move independently of compute. Any production migration requires a separately reviewed backup and recovery plan.
- Actual account capacity, free/used scope and photo/video eligibility must be discovered and verified; no fixed allowance is assumed.
- Existing Amazon copies are retained. Their overlap with current originals is unknown; upstream metadata edits can change exact file hashes.
- First release: configured filesystem photo sources and Amazon inventory/reconciliation. An Immich API adapter is optional later work, not a prerequisite for filesystem protection.
- Integration choice remains open; the standalone amazon_photos library needs fixes/review before use.
- Video upload, bidirectional sync, deletion, cloud cleanup and general server backups are out of the initial scope.

Priority **MUST** means required for release; **SHOULD** means a documented tradeoff may defer it. All requirements map to acceptance scenarios.

## Content safety

| ID | Priority | Requirement |
|---|---|---|
| SAFE-01 | MUST | Never modify, rename, delete, move or write metadata into source originals or sidecars. All container source mounts are read-only. |
| SAFE-02 | MUST | Never delete/trash cloud originals or propagate source deletions, missing albums, excluded files or missing mounts into cloud removal. No destructive operation is exposed by the worker. |
| SAFE-03 | MUST | Inventory and dry-run perform no cloud uploads, folder/album creation or metadata changes. Read-only account calls must be explicitly identified and tested. |
| SAFE-04 | MUST | Missing mounts, unreadable sources, incomplete cloud inventories, corrupt state, missing hashes and authentication errors cannot silently become an empty or successful inventory. |
| SAFE-05 | MUST | An empty/misconfigured source is reported as an error or explicit reviewed empty dataset; it never triggers deletion or claims coverage. |
| SAFE-06 | MUST | Tests use synthetic fixtures; live pilots use an explicitly selected small dataset. Preserve the old Amazon collection during reconciliation. |

## Inventory and reconciliation

| ID | Priority | Requirement |
|---|---|---|
| INV-01 | MUST | Enumerate every included source with stable dataset IDs, relative path, size, type, timestamps, current SHA256 and change detection. Handle symlinks/mount escapes explicitly without reading outside configured roots. |
| INV-02 | MUST | Keep photo originals, video/motion components, sidecars, generated derivatives, inbox and review buckets separately visible. Record exclusions and reasons; excluded content is not protected content. |
| INV-03 | MUST | Obtain a complete paginated cloud inventory with node IDs, available checksums/sizes/type/status and verified completeness evidence. If completeness cannot be established, block bulk upload and label the result partial. |
| INV-04 | MUST | Reconcile existing cloud content before upload. Filename or visual resemblance alone cannot prove identical originals. Use comparable checksum/size evidence and retrieval where needed; classify unresolved matches for review. |
| INV-05 | MUST | Account for metadata edits/provenance from the curator without treating pre-edit and post-edit hashes as identical bytes. Explain what version a cloud copy protects. |
| INV-06 | MUST | Inventory/checkpoint records are private persistent state, backed up separately from originals. No private filenames, GPS data or account inventories in Git or routine console logs. |
| INV-07 | SHOULD | Support incremental inventory/hash caching with invalidation on relevant file changes, bounded I/O and an explicit full verification option. |

## Upload and recovery evidence

| ID | Priority | Requirement |
|---|---|---|
| UP-01 | MUST | Default to inventory/dry-run. Upload execution consumes an explicit, bounded plan identifying datasets, target account/region, exclusions and operation limits. |
| UP-02 | MUST | Upload exact original bytes only; never silently substitute previews, thumbnails, transcoded output or metadata-stripped copies. Unsupported files remain visible as unprotected. |
| UP-03 | MUST | Repeated runs do not re-upload verified identical content. Different source/Immich IDs may map to the same verified content. Unknown outcomes require reconciliation before retry. |
| UP-04 | MUST | Maintain transactional durable intent/result checkpoints per operation. Recover safely from process/host restarts and lost acknowledgements without assuming success or duplicating uploads blindly. |
| UP-05 | MUST | Use distinct planned, already-verified, uploaded-unverified, verified, excluded, unknown and failed states. HTTP409 alone, a returned node ID or an attempted-upload count is not verification. |
| UP-06 | MUST | Validate remote size/checksum evidence and retrieve original bytes for defined verification samples and all ambiguous cases. Distinguish provider evidence, sampled retrieval and full retrieval coverage. |
| UP-07 | MUST | Produce a completeness report per dataset and run, with counts/bytes, excluded/unknown/failed items, verification level and timestamps. Never state fully backed up while required content is unresolved. |
| UP-08 | MUST | Default uploads to eligible photos only. Verify account quota/eligibility and reserve headroom; do not infer video allowance from unlimited photo storage. Stop safely on quota failures. |
| UP-09 | MUST | Unsupported formats, Live Photo/video components and sidecars have explicit coverage gaps or a separately verified destination; they cannot disappear from reporting. |

## Authentication, network and privacy

| ID | Priority | Requirement |
|---|---|---|
| SEC-01 | MUST | Enforce TLS verification for every client, upload, download and redirect; no verify=False fallback. |
| SEC-02 | MUST | Correctly map account region/cookies to verified web/content endpoints, including UK co.uk. Never send credentials to arbitrary endpoints or unapproved redirect hosts. |
| SEC-03 | MUST | Read credentials from a private mounted file/secret, not image layers, command arguments, Git or application reports. Document private refresh/revocation procedures. |
| SEC-04 | MUST | Authentication expiry stops affected work and produces actionable status; never report an expired session as an empty library. Do not expose cookie values or raw sensitive API bodies in logs. |
| SEC-05 | MUST | Separate account identities in state; refuse accidental account switching or applying a plan to a different account/library. |
| SEC-06 | SHOULD | Use the smallest viable account/API access and allowlist operations; do not expose destructive client capabilities merely because a dependency offers them. |

## Container, operation and portability

| ID | Priority | Requirement |
|---|---|---|
| OPS-01 | MUST | Run in a standalone container with non-root user, read-only root filesystem, dropped capabilities, no privileged mode, Docker socket or unnecessary published ports. |
| OPS-02 | MUST | Configure source locations/dataset IDs separately from code. Preserve stable logical paths/identities across a later source-storage storage move and require an inventory reconciliation after cutover. |
| OPS-03 | MUST | Persist state independently of the container lifecycle; protect and restore-test it through the operator's application-backup process. |
| OPS-04 | MUST | Bound memory, scratch space, concurrency, retries and I/O. Stream large files and exclude generated media unless explicitly required. |
| OPS-05 | MUST | Prevent overlapping conflicting runs; use timeouts/backoff and safe shutdown. Different accounts/datasets must not corrupt shared state. |
| OPS-06 | MUST | Publish privacy-safe run status, errors, progress and staleness suitable for the external portal/monitoring; document failure and capacity alerts. |
| OPS-07 | MUST | Reproducible image/dependency versions, provenance, retained upstream notices, build/setup/configuration and rollback/recovery instructions accompany releases. |
| OPS-08 | MUST | A fresh-container/state restore and resumed-run test pass before unattended scheduling. Add a schedule only after the pilot/acceptance review. |

## Release gates

1. Reviewed requirements and decisions.
2. Synthetic offline acceptance tests; reviewed dependency/transport behavior.
3. Reproducible container build and local read-only fixture tests.
4. Explicit private account authorisation and read-only inventory pilot.
5. Old-library reconciliation and bounded original-upload/download pilot.
6. Failure/restart/state recovery tests, content-gap review and operational documentation.
7. Only then enable unattended execution.

## Non-goals

No source cleanup; no Amazon trash/purge; no bidirectional sync; no replacement for encrypted server/app backups; no automatic source-storage migration; no implied off-site video/document protection.
