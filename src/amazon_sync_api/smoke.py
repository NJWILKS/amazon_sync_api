"""Manual live check: synthetic image upload and original retrieval under test/UTC."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
from urllib.parse import urlencode
import zlib

from .amazon import Amazon, Transport
from .core import BackupError


def sample_png():
    """Generate a valid 2x2 RGB PNG with no personal content or metadata."""
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)))
    pixels = b"\x00\xff\x00\x00\x00\xff\x00\x00\x00\x00\xff\xff\xff\xff"
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


def create_test_folder(provider):
    # Test-only account discovery; production connect still requires expected identity.
    result = provider.transport.request("GET", provider.base + "/nodes?" + urlencode(
        {"filters": "isRoot:true", "asset": "ALL", "tempLink": "false",
         "resourceVersion": "V2", "ContentType": "JSON"}))
    data = result.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise BackupError("Could not establish one account root")
    node = data[0]
    if not all(isinstance(node.get(k), str) and node[k] for k in ("id", "ownerId")):
        raise BackupError("Account root is missing identifiers")
    provider.root_id, provider.owner = node["id"], node["ownerId"]
    name = "test"
    folder = provider.ensure_folder(provider.root_id, name)
    if provider.find(provider.root_id, name, "FOLDER") != folder:
        raise BackupError("Test folder could not be independently read back")
    return folder


def verify_image(provider, workspace, timestamp=None):
    stamp = timestamp or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if len(stamp) != 14 or not stamp.isascii() or not stamp.isdigit():
        raise BackupError("Invalid test timestamp")
    parent = create_test_folder(provider)
    if provider.find(parent, stamp, "FOLDER"):
        raise BackupError("Timestamp folder already exists; start a new run")
    folder = provider.ensure_folder(parent, stamp)
    if provider.find(parent, stamp, "FOLDER") != folder:
        raise BackupError("Timestamp folder could not be independently read back")
    source = workspace / "sample.png"
    content = sample_png()
    source.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    node = provider.upload(folder, "sample.png", source)
    if not node or provider.find_file(folder, "sample.png") != node:
        raise BackupError("Uploaded image could not be independently read back")
    if provider.original_sha256(node) != expected:
        raise BackupError("Downloaded original SHA-256 does not match synthetic image")
    if source.read_bytes() != content:
        raise BackupError("Synthetic source changed during test")
    return "test/" + stamp + "/sample.png"


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
            target = verify_image(Amazon(Transport("uk", path)), Path(tmp))
        print("PASS: upload and downloaded original SHA-256 verified at " + target)
        return 0
    except BackupError as exc:
        print("FAIL: " + str(exc))
        return 1
    except Exception:
        print("FAIL: Check cookie JSON and provider compatibility; no secret values logged")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
