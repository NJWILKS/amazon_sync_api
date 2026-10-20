# amazon_sync_api

A containerised, upload-only backup worker for existing photo libraries and Amazon Photos.

**Status: requirements baseline v0.1 — draft for review. No application implementation, deployment or live Amazon connection.**

Start with [what the API evidence actually supports](docs/api-capabilities.md), then [requirements](docs/requirements.md), [acceptance tests](docs/acceptance.md), [decisions and open questions](docs/decisions.md), and [delivery milestones](docs/roadmap.md).

The project separates source content, application state and off-site evidence. It must reconcile an existing Amazon collection, preserve originals and never propagate deletions. Deployment hosts and source-storage locations are configuration, not code. Moving source storage must require reviewed configuration changes rather than rebuilding the worker.

`trevorhobenshield/amazon_photos` is an evaluated integration candidate, not a selected or installed dependency. See [upstream evaluation](docs/upstream.md). This repository is a new project, not a fork of that library.

No private photos, inventories, cookies, tokens or credential-bearing configuration belong in Git.
