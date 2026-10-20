"""Manual live smoke check: authenticate and create/verify one test folder."""
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlencode

from .amazon import Amazon, Transport
from .core import BackupError


def create_test_folder(provider):
    # Test-only account discovery; production connect still requires expected identity.
    result = provider.transport.request("GET", provider.base + "/nodes?" + urlencode(
        {"filters": "isRoot:true", "resourceVersion": "V2", "ContentType": "JSON"}))
    data = result.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise BackupError("Could not establish one account root")
    node = data[0]
    if not all(isinstance(node.get(k), str) and node[k] for k in ("id", "ownerId")):
        raise BackupError("Account root is missing identifiers")
    provider.root_id, provider.owner = node["id"], node["ownerId"]
    name = "integration-test-amazon-sync-api"
    folder = provider.ensure_folder(provider.root_id, name)
    if provider.find(provider.root_id, name, "FOLDER") != folder:
        raise BackupError("Test folder could not be independently read back")


def main():
    try:
        # Temporary file is private and removed on exit; never log the secret or response.
        with tempfile.TemporaryDirectory(prefix="amazon-smoke-") as tmp:
            path = Path(tmp) / "cookies.json"
            secret = os.environ.pop("AMAZON_PHOTOS_COOKIES", "")
            cookies = json.loads(secret)
            if not isinstance(cookies, dict):
                raise ValueError()
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(cookies, stream)
            create_test_folder(Amazon(Transport("uk", path)))
        print("PASS: Amazon connection and test-folder read-back verified")
        return 0
    except BackupError as exc:
        print("FAIL: " + str(exc))
        return 1
    except Exception:
        print("FAIL: Check cookie JSON and provider compatibility; no secret values logged")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
