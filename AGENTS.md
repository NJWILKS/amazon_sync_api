# Project working instructions

Read docs/requirements.md, docs/acceptance.md and docs/decisions.md before implementation or requirements changes. Requirements are a draft unless explicitly marked agreed with evidence; do not invent user approval.

Keep stable requirement IDs and link implementation/tests to them. Distinguish source inspection, mocked tests, live verification and recovery evidence. Never claim a configured upload, remote object or cached inventory proves recoverability.

Keep secrets, private filenames/GPS metadata, real inventories, account cookies and photo/database contents out of Git and logs. Use synthetic fixtures in tests. Preserve third-party notices/provenance if upstream code is adopted.

Sources must remain read-only. Do not introduce source/cloud deletion or implicit write operations into inventory/dry-run paths. A test must never operate on personal originals; use explicit synthetic fixtures.

Keep application state and content protection separate. Update affected setup/recovery documentation and docs/change-log.md after material changes. Keep private deployment details outside this public repository. Do not change an operator's storage or disconnect remote sessions as part of development.

