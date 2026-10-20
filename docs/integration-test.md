# Real Amazon integration test

This test is implemented but has not been run against Amazon. Offline fixture guard passed on Windows on 20 October 2026. Ordinary discovery skips the live test unless explicitly enabled.

The test connects to the expected account, creates three configured test roots, preserves nested and empty folders, uploads six generated PNG fixtures, retrieves originals for SHA-256 verification and repeats the run expecting zero new uploads. It independently checks the destination tree. Previously verified fixtures may be reused, so the first run need not create six new objects.

Personal source paths from configuration are never read: the test substitutes newly generated temporary trees. Roots must start with `integration-test-`. The entire fixture payload is under 1 KiB. No cloud cleanup or deletion is performed; keep those roots and the private checkpoint database to investigate failures. Do not run simultaneous jobs with the same roots/state.

## Private prerequisites

Copy `config.integration.example.toml` to an operator-only `*.local.toml` file outside source trees. Set the independently confirmed Amazon owner ID, private cookies JSON path and a dedicated checkpoint database path. The experimental UK adapter requires `session-id`, `ubid-acbuk` and `at-acbuk` cookie entries; the US adapter uses the corresponding `main` suffix. Do not commit or paste cookie values into chat, logs or issues. Obtain session credentials privately; no credential capture helper is included yet. Restrict access to the files to the operator.

Run from the project directory with the package installed, or with `PYTHONPATH=src`:

```sh
AMAZON_SYNC_LIVE=1 AMAZON_SYNC_LIVE_CONFIG=/private/integration.local.toml \
  python -m unittest discover -s tests -p test_live_amazon.py -v
```

PowerShell:

```powershell
$env:PYTHONPATH = 'src'
$env:AMAZON_SYNC_LIVE = '1'
$env:AMAZON_SYNC_LIVE_CONFIG = 'C:\private\integration.local.toml'
python -m unittest discover -s tests -p test_live_amazon.py -v
Remove-Item Env:AMAZON_SYNC_LIVE
Remove-Item Env:AMAZON_SYNC_LIVE_CONFIG
```

If opted in without a config, the test fails rather than silently skipping. Expired credentials, account mismatch, API incompatibility, conflicting objects or retrieval mismatches fail the test. A passed test establishes only this small fixture contract, not entitlement, large-library correctness, metadata-modified duplicate matching, long-term retention or complete application recovery. Record execution date and code version before claiming live validation. After failure retain cloud objects/state; no automatic reset or destructive retry.

## GitHub connection/folder smoke test
Run Actions > Amazon live connection test > Run workflow on main. The manual workflow uses AMAZON_PHOTOS_COOKIES (complete UK cookie JSON). No expected account ID or PC configuration is required. It discovers one authenticated root and creates/reuses integration-test-amazon-sync-api, then reads it back. It uploads no photos and deletes nothing. Cookies go into a mode-600 temporary runner file, removed on process exit. No credential/account values, response bodies or artifacts are logged. Live execution pending; offline validation: 20 passed, two skipped on Windows. Full-tree live testing remains a separate opt-in test.
