# Collections

User-requested model, 20 October 2026: one service handles multiple independent collections. Each collection maps one local source tree to one configured Amazon root folder. Examples are `immich`, `captures` and `photoscans`; names and source paths are configurable. These are application collections, not Amazon albums.

See `config.example.toml`. Collection IDs and destination roots must be unique, including case differences. Nested and empty directories are preserved by the prototype. Files with the same name in different directories remain separate. Checkpoints are bound to the account and each collection's destination root.

The current prototype plans all sources before contacting Amazon. Planning reads files and hashes eligible photos, without opening credentials, creating state or contacting Amazon. Default limits are 100 photos and 1 GiB per collection; these are pilot limits, not an unattended library deployment. Unsupported files are counted as exclusions and prevent a complete result. Xbox videos, sidecars and other excluded content require separate protection.

Execution checks the expected account identity before creating folders. Existing same-path files are retrieved and compared by SHA-256; different content stops execution without overwriting it. Each new upload is retrieved and hashed before its checkpoint is marked verified. An uncertain upload outcome blocks blind retries. No delete or trash operation is implemented.

## Validation status

Offline synthetic tests exercise independent roots, repeated names, nested trees, reruns, conflicts and interrupted uploads. They do not establish that Amazon accepts the adapter's requests. Live authentication, API compatibility, quota, retention and a full recovery remain unverified. This prototype does not reconcile an old account globally or identify visually equivalent photos after metadata changes.

## Running locally

Use Python 3.11 or later. Copy the example to a private configuration outside source trees. Keep account cookies and the SQLite state outside Git and outside every source tree.

```sh
python -m pip install .
amazon-sync plan --config /private/collections.toml
```

Only after reviewing a synthetic fixture plan and privately preparing credentials:

```sh
amazon-sync execute --config /private/collections.toml
```

Do not run live tests against personal originals. There is no installed scheduler or household deployment. If execution fails, retain the state file and cloud objects. Investigate the uncertain result rather than resetting checkpoints to force a retry. Source originals remain the recovery source until independent content recovery has been demonstrated.
