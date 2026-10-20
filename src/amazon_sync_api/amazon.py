"""Narrow experimental Amazon web adapter. No trash/delete/metadata-mutation API."""
import hashlib
import http.client
import json
from pathlib import Path
import ssl
from urllib.parse import quote, urlencode, urlsplit

from .core import BackupError, UnknownOutcome, component

REGIONS = {
    "uk": ("www.amazon.co.uk", "content-eu.drive.amazonaws.com", "acbuk"),
    "us": ("www.amazon.com", "content-na.drive.amazonaws.com", "main"),
}


class Transport:
    """TLS-only, bounded requests; never forward cookies to arbitrary redirect hosts."""
    def __init__(self, region, cookies_file):
        self.web, self.content, suffix = REGIONS[region]
        try:
            cookies = json.loads(Path(cookies_file).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            raise BackupError("Could not load private cookie file") from None
        required = ("session-id", "ubid-" + suffix, "at-" + suffix)
        if any(not isinstance(cookies.get(k), str) or not cookies[k]
               or any(c in cookies[k] for c in "\r\n;") for k in required):
            raise BackupError("Required regional session cookies are missing or invalid")
        self.cookie = "; ".join(k + "=" + cookies[k] for k in required)
        self.session_id = cookies["session-id"]
        self.context = ssl.create_default_context()

    def request(self, method, url, *, payload=None, file=None, sha=False):
        if method not in {"GET", "POST"}:
            raise BackupError("Unsupported request method")
        initial = urlsplit(url)
        if initial.hostname not in {self.web, self.content}:
            raise BackupError("Unapproved initial endpoint")
        for redirect in range(6):
            parsed = urlsplit(url)
            host = parsed.hostname or ""
            if (parsed.scheme != "https" or parsed.username or parsed.password
                    or parsed.port not in (None, 443)
                    or not (host in {self.web, self.content} or
                            (method == "GET" and host.endswith(".amazonaws.com")))):
                raise BackupError("Unapproved HTTPS endpoint")
            headers = {"User-Agent": "amazon-sync-api/0.1"}
            if host in {self.web, self.content}:
                headers.update(Cookie=self.cookie, **{"x-amzn-sessionid": self.session_id})
            body = json.dumps(payload).encode() if payload is not None else None
            if body is not None:
                headers.update({"Content-Type": "application/json", "Content-Length": str(len(body))})
            if file is not None:
                headers.update({"Content-Type": "application/octet-stream",
                                "Content-Length": str(file.stat().st_size)})
            connection = http.client.HTTPSConnection(host, timeout=60, context=self.context)
            try:
                path = parsed.path + ("?" + parsed.query if parsed.query else "")
                connection.putrequest(method, path)
                for key, value in headers.items():
                    connection.putheader(key, value)
                connection.endheaders()
                if file is not None:
                    with file.open("rb") as source:
                        for block in iter(lambda: source.read(64 * 1024), b""):
                            connection.send(block)
                elif body is not None:
                    connection.send(body)
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    if method != "GET":
                        raise UnknownOutcome("Write redirected; reconcile result")
                    location = response.getheader("Location")
                    if not location or not location.startswith("https://"):
                        raise BackupError("Invalid download redirect")
                    url = location
                    continue
                if response.status in {401, 403}:
                    raise BackupError("Amazon session is expired or access was refused")
                if response.status == 409:
                    raise UnknownOutcome("Conflict requires content reconciliation")
                if not 200 <= response.status < 300:
                    raise BackupError("Amazon request failed")
                if sha:
                    h = hashlib.sha256()
                    for block in iter(lambda: response.read(64 * 1024), b""):
                        h.update(block)
                    return h.hexdigest()
                raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise BackupError("Metadata response exceeded limit")
                try:
                    result = json.loads(raw)
                except ValueError:
                    raise BackupError("Amazon returned invalid metadata") from None
                if not isinstance(result, dict):
                    raise BackupError("Unexpected metadata structure")
                return result
            except (OSError, http.client.HTTPException):
                if method != "GET":
                    raise UnknownOutcome("Write transport failed; reconcile result") from None
                raise BackupError("Read transport failed") from None
            finally:
                connection.close()
        raise BackupError("Too many download redirects")


class Amazon:
    def __init__(self, transport):
        self.transport = transport
        self.base = "https://" + transport.web + "/drive/v1"
        self.root_id = None
        self.owner = None

    def connect(self, expected_owner):
        if not expected_owner or expected_owner.startswith("SET_"):
            raise BackupError("Configure the expected account owner before connecting")
        result = self.transport.request("GET", self.base + "/nodes?" + urlencode(
            {"filters": "isRoot:true", "resourceVersion": "V2", "ContentType": "JSON"}))
        data = result.get("data")
        if not isinstance(data, list) or len(data) != 1:
            raise BackupError("Could not establish one account root")
        node = data[0]
        if node.get("ownerId") != expected_owner or not isinstance(node.get("id"), str):
            raise BackupError("Account identity could not be verified")
        self.owner, self.root_id = expected_owner, node["id"]

    def children(self, parent):
        rows, ids, expected = [], set(), None
        for offset in range(0, 10000, 200):
            page = self.transport.request("GET", self.base + "/nodes/" + quote(parent, safe="") +
                "/children?" + urlencode({"limit": 200, "offset": offset, "resourceVersion": "V2"}))
            total, data = page.get("count"), page.get("data")
            if type(total) is not int or total < 0 or total > 9999 or not isinstance(data, list):
                raise BackupError("Folder listing completeness is unproven")
            if expected is None:
                expected = total
            if total != expected:
                raise BackupError("Folder listing changed during pagination")
            for item in data:
                node = item.get("id")
                if not isinstance(node, str) or node in ids:
                    raise BackupError("Folder listing contains missing or duplicate identifiers")
                ids.add(node)
                rows.append(item)
            if len(rows) == expected:
                return rows
            if not data or len(rows) > expected:
                raise BackupError("Folder listing is incomplete")
        raise BackupError("Folder listing exceeded tested limit")

    def find(self, parent, name, kind):
        matches = [x for x in self.children(parent) if x.get("name", "").casefold() == name.casefold()]
        if not matches:
            return None
        if (len(matches) != 1 or matches[0].get("kind") != kind
                or matches[0].get("name") != name
                or matches[0].get("status", "AVAILABLE") != "AVAILABLE"):
            raise BackupError("Destination name is ambiguous or unavailable")
        return matches[0]["id"]

    def ensure_folder(self, parent, name):
        component(name)
        found = self.find(parent, name, "FOLDER")
        if found:
            return found
        result = self.transport.request("POST", self.base + "/nodes",
            payload={"kind": "FOLDER", "name": name, "parents": [parent],
                     "resourceVersion": "V2", "ContentType": "JSON"})
        node = result.get("id")
        if not isinstance(node, str) or not node:
            raise UnknownOutcome("Folder creation result is unresolved")
        return node

    def find_file(self, parent, name):
        return self.find(parent, name, "FILE")

    def upload(self, parent, name, source):
        component(name)
        result = self.transport.request("POST",
            "https://" + self.transport.content + "/cdproxy/nodes?" +
            urlencode({"name": name, "kind": "FILE", "parentNodeId": parent}), file=source)
        node = result.get("id")
        if not isinstance(node, str) or not node:
            raise UnknownOutcome("Upload acknowledgement has no identifier")
        return node

    def original_sha256(self, node):
        return self.transport.request("GET", self.base + "/nodes/" + quote(node, safe="") +
            "/contentRedirection?" + urlencode({"querySuffix": "?download=true",
                                               "ownerId": self.owner}), sha=True)
