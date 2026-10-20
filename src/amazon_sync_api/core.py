"""Configuration, read-only planning, durable checkpoints and tree orchestration."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import sqlite3
import stat
import tomllib


class BackupError(RuntimeError):
    """Safe diagnostic: no credentials or private paths in the message."""


class UnknownOutcome(BackupError):
    pass


def component(name):
    if (not isinstance(name, str) or not name or name in {".", ".."}
            or any(c in name for c in "/\\") or any(ord(c) < 32 for c in name)):
        raise BackupError("Invalid remote path component")
    return name


@dataclass(frozen=True)
class Collection:
    id: str
    source: Path
    remote_root: str


@dataclass(frozen=True)
class Settings:
    region: str
    expected_owner_id: str
    cookies_file: Path
    state_file: Path
    collections: tuple
    max_files: int = 100
    max_bytes: int = 1024 * 1024 * 1024


def load_config(path):
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text(encoding="utf-8-sig"))
    def location(value):
        p = Path(value).expanduser()
        return p if p.is_absolute() else path.parent / p
    collections = tuple(Collection(component(t["id"]), location(t["source"]),
                           component(t["remote_root"])) for t in raw.get("collections", []))
    if not collections:
        raise BackupError("At least one collection is required")
    for attr in ("id", "remote_root"):
        values = [getattr(t, attr).casefold() for t in collections]
        if len(values) != len(set(values)):
            raise BackupError("Collection identities and roots must be unique")
    region = raw.get("region", "uk")
    if region not in {"uk", "us"}:
        raise BackupError("Unsupported region")
    limits = raw.get("limits", {})
    settings = Settings(region, raw.get("expected_owner_id", ""),
        location(raw["cookies_file"]), location(raw["state_file"]), collections,
        limits.get("max_files", 100), limits.get("max_bytes", 1024 ** 3))
    if any(type(x) is not int or x <= 0 for x in (settings.max_files, settings.max_bytes)):
        raise BackupError("Limits must be positive integers")
    # Prevent accidental credential/state upload through a configured source.
    for collection in collections:
        root = collection.source.resolve()
        if any(p.resolve().is_relative_to(root) for p in
               (settings.cookies_file, settings.state_file, path)):
            raise BackupError("Config, credentials and state must be outside sources")
    return settings


@dataclass(frozen=True)
class Item:
    relative: str
    size: int
    sha256: str
    identity: tuple


@dataclass(frozen=True)
class Plan:
    collection: Collection
    directories: tuple
    files: tuple
    excluded: tuple


PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff",
                    ".webp", ".gif", ".bmp", ".dng", ".cr2", ".cr3", ".nef", ".arw"}


def identity(path):
    s = path.lstat()
    if not stat.S_ISREG(s.st_mode):
        raise BackupError("Source file is not a regular file")
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(64 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def plan_tree(collection, max_files=100, max_bytes=1024 ** 3):
    source = collection.source
    if source.is_symlink() or not source.is_dir() or source.resolve() == Path(source.anchor):
        raise BackupError("Source collection must be a real directory below a filesystem root")
    dirs, items, excluded = [], [], []
    total = 0
    def onerror(_):
        raise BackupError("Source enumeration failed")
    for parent, directory_names, file_names in os.walk(source, followlinks=False, onerror=onerror):
        directory_names.sort()
        file_names.sort()
        rel_parent = Path(parent).relative_to(source)
        for name in directory_names + file_names:
            component(name)
            if (Path(parent) / name).is_symlink():
                raise BackupError("Symlinks are not supported in this slice")
        for name in directory_names:
            dirs.append((rel_parent / name).as_posix())
        for name in file_names:
            p = Path(parent) / name
            rel = (rel_parent / name).as_posix()
            before = identity(p)
            if p.suffix.lower() not in PHOTO_EXTENSIONS:
                excluded.append(rel)
                continue
            if len(items) + 1 > max_files or total + before[2] > max_bytes:
                raise BackupError("Configured operation limit exceeded")
            sha = digest(p)
            if before != identity(p):
                raise BackupError("Source changed during planning")
            total += before[2]
            items.append(Item(rel, before[2], sha, before))
    if not items:
        raise BackupError("No eligible photo files found")
    # Reject ambiguous names before cloud mutation, including case-only collisions.
    all_names = [x.casefold() for x in dirs] + [x.relative.casefold() for x in items]
    if len(set(all_names)) != len(all_names):
        raise BackupError("Source names are ambiguous for a remote tree")
    return Plan(collection, tuple(dirs), tuple(items), tuple(excluded))


class State:
    def __init__(self, path, owner):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.path)
        if os.name != "nt":
            self.path.chmod(0o600)
        self.db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS files "
            "(collection TEXT, path TEXT, sha TEXT, status TEXT, node TEXT, "
            "PRIMARY KEY(collection,path))")
        prior = self.db.execute("SELECT value FROM metadata WHERE key='owner'").fetchone()
        if prior and prior[0] != owner:
            self.close()
            raise BackupError("State belongs to a different account")
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('owner', ?)", (owner,))
        self.db.commit()

    def bind_collection(self, collection):
        key = "collection:" + collection.id
        prior = self.db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        if prior and prior[0] != collection.remote_root:
            raise BackupError("Collection root changed; use a separately reviewed state")
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES (?, ?)",
                        (key, collection.remote_root))
        self.db.commit()

    def get(self, collection, path):
        return self.db.execute("SELECT sha,status,node FROM files WHERE collection=? AND path=?",
                               (collection, path)).fetchone()

    def put(self, collection, item, status, node=None):
        self.db.execute("INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)",
                        (collection, item.relative, item.sha256, status, node))
        self.db.commit()

    def close(self):
        self.db.close()


def run_collection(plan, provider, state):
    """Provider has only connect/read/create-folder/upload methods, never delete."""
    collection = plan.collection
    # Validate the whole plan before any cloud writes.
    for item in plan.files:
        if identity(collection.source / item.relative) != item.identity:
            raise BackupError("Source changed after planning")
    state.bind_collection(collection)
    folders = {"": provider.ensure_folder(provider.root_id, collection.remote_root)}
    for directory in plan.directories:
        relative = Path(directory)
        parent = relative.parent.as_posix()
        folders[directory] = provider.ensure_folder(
            folders["" if parent == "." else parent], relative.name)
    result = {"collection": collection.id, "uploaded": 0, "already_verified": 0,
              "verified": 0, "excluded": len(plan.excluded),
              "complete": not plan.excluded}
    for item in plan.files:
        source = collection.source / item.relative
        relative = Path(item.relative)
        parent = relative.parent.as_posix()
        parent_id = folders["" if parent == "." else parent]
        if identity(source) != item.identity or digest(source) != item.sha256:
            raise BackupError("Source changed before upload")
        prior = state.get(collection.id, item.relative)
        node = provider.find_file(parent_id, relative.name)
        if node:
            if provider.original_sha256(node) != item.sha256:
                raise BackupError("Existing destination contains different content")
            result["already_verified"] += 1
        else:
            if prior and prior[1] in {"uploading", "unknown"}:
                raise UnknownOutcome("Previous upload is unresolved; reconcile before retry")
            state.put(collection.id, item, "uploading")
            try:
                node = provider.upload(parent_id, relative.name, source)
                if not node or provider.original_sha256(node) != item.sha256:
                    raise UnknownOutcome("Uploaded original could not be verified")
                if identity(source) != item.identity or digest(source) != item.sha256:
                    raise UnknownOutcome("Source changed during upload")
            except Exception:
                state.put(collection.id, item, "unknown")
                raise UnknownOutcome("Upload result is unresolved") from None
            result["uploaded"] += 1
        if identity(source) != item.identity or digest(source) != item.sha256:
            raise BackupError("Source changed during verification")
        state.put(collection.id, item, "verified", node)
        result["verified"] += 1
    return result


def run(settings, provider):
    # Plan all collections first; a bad second source must not allow first-source writes.
    plans = [plan_tree(t, settings.max_files, settings.max_bytes) for t in settings.collections]
    provider.connect(settings.expected_owner_id)
    state = State(settings.state_file, settings.expected_owner_id)
    try:
        return [run_collection(p, provider, state) for p in plans]
    finally:
        state.close()

