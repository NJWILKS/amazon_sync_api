import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from amazon_sync_api.core import (BackupError, Collection, Settings, State, UnknownOutcome,
                                  digest, load_config, plan_tree, run)
from amazon_sync_api.amazon import Amazon, Transport

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a0S8AAAAASUVORK5CYII=")


class FakeProvider:
    root_id = "root"
    def __init__(self):
        self.folders = {}
        self.files = {}
        self.operations = []
        self.content = {}
        self.fail_upload = False
    def connect(self, owner):
        if owner != "owner":
            raise BackupError("Wrong owner")
        self.operations.append(("connect",))
    def ensure_folder(self, parent, name):
        key = (parent, name)
        if key not in self.folders:
            self.folders[key] = "d" + str(len(self.folders))
            self.operations.append(("folder", parent, name))
        return self.folders[key]
    def find_file(self, parent, name):
        return self.files.get((parent, name))
    def upload(self, parent, name, source):
        self.operations.append(("upload", parent, name))
        if self.fail_upload:
            raise UnknownOutcome("Unknown acknowledgement")
        node = "f" + str(len(self.files))
        self.files[parent, name] = node
        self.content[node] = source.read_bytes()
        return node
    def original_sha256(self, node):
        return hashlib.sha256(self.content[node]).hexdigest()


class TreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.collections = []
        for name in ("immich", "captures", "photoscans"):
            src = self.base / name
            (src / "nested" / "empty").mkdir(parents=True)
            (src / "same.png").write_bytes(PNG)
            (src / "nested" / "same.png").write_bytes(PNG)
            self.collections.append(Collection(name, src, name))
        self.settings = Settings("uk", "owner", self.base / "cookies.json",
                                  self.base / "state.sqlite3", tuple(self.collections))

    def test_three_configured_roots_preserve_nested_and_empty_tree_and_source(self):
        before = {str(p): digest(p) for c in self.collections for p in c.source.rglob("*.png")}
        provider = FakeProvider()
        report = run(self.settings, provider)
        self.assertEqual([r["collection"] for r in report], ["immich", "captures", "photoscans"])
        self.assertEqual(sum(r["verified"] for r in report), 6)
        self.assertEqual(sum(r["uploaded"] for r in report), 6)
        self.assertTrue(all(r["complete"] for r in report))
        for name in ("immich", "captures", "photoscans"):
            root = provider.folders["root", name]
            nested = provider.folders[root, "nested"]
            self.assertIn((nested, "empty"), provider.folders)
            self.assertNotEqual(provider.files[root, "same.png"], provider.files[nested, "same.png"])
        self.assertEqual(before, {str(p): digest(p) for c in self.collections for p in c.source.rglob("*.png")})

    def test_second_run_verifies_without_reuploading(self):
        p = FakeProvider()
        run(self.settings, p)
        result = run(self.settings, p)
        self.assertEqual(sum(r["uploaded"] for r in result), 0)
        self.assertEqual(sum(r["already_verified"] for r in result), 6)

    def test_dry_plan_never_needs_provider_or_credentials(self):
        result = plan_tree(self.collections[0])
        self.assertEqual(len(result.files), 2)
        self.assertFalse(self.settings.cookies_file.exists())
        self.assertFalse(self.settings.state_file.exists())

    def test_bad_second_source_prevents_any_cloud_calls(self):
        self.collections[1].source.rename(self.base / "moved")
        p = FakeProvider()
        with self.assertRaises(BackupError):
            run(self.settings, p)
        self.assertEqual(p.operations, [])

    def test_limits_prevent_cloud_calls(self):
        p = FakeProvider()
        limited = Settings("uk", "owner", self.settings.cookies_file,
                           self.settings.state_file, tuple(self.collections), max_files=1)
        with self.assertRaises(BackupError):
            run(limited, p)
        self.assertEqual(p.operations, [])

    def test_unsupported_files_are_visible_not_silently_complete(self):
        (self.collections[0].source / "movie.mp4").write_bytes(b"not-a-photo")
        result = run(self.settings, FakeProvider())
        self.assertEqual(result[0]["excluded"], 1)
        self.assertFalse(result[0]["complete"])

    def test_same_name_different_bytes_is_not_overwritten(self):
        p = FakeProvider()
        run(self.settings, p)
        node = p.files[p.folders["root", "immich"], "same.png"]
        p.content[node] = b"different"
        with self.assertRaises(BackupError):
            run(self.settings, p)
        self.assertEqual(p.content[node], b"different")

    def test_unknown_write_is_not_retried_blindly(self):
        p = FakeProvider()
        p.fail_upload = True
        with self.assertRaises(UnknownOutcome):
            run(self.settings, p)
        p.fail_upload = False
        prior = sum(x[0] == "upload" for x in p.operations)
        with self.assertRaises(UnknownOutcome):
            run(self.settings, p)
        self.assertEqual(prior, sum(x[0] == "upload" for x in p.operations))

    def test_account_state_isolation(self):
        s = State(self.settings.state_file, "owner")
        s.close()
        with self.assertRaises(BackupError):
            State(self.settings.state_file, "other")

    def test_unsafe_symlink_is_rejected(self):
        try:
            (self.collections[0].source / "link.png").symlink_to(self.base / "outside")
        except OSError:
            self.skipTest("Symlink privilege unavailable on this host")
        with self.assertRaises(BackupError):
            plan_tree(self.collections[0])

    def test_config_supports_three_collections_and_relative_paths(self):
        config = self.base / "config.toml"
        config.write_text('region="uk"\nexpected_owner_id="owner"\ncookies_file="cookies.json"\n'
                          'state_file="checkpoint.db"\n' + "".join(
            '[[collections]]\nid="' + name + '"\nsource="' + name +
            '"\nremote_root="' + name + '"\n' for name in ("immich", "captures", "photoscans")))
        result = load_config(config)
        self.assertEqual(len(result.collections), 3)
        self.assertEqual(result.collections[0].source, self.collections[0].source)

    def test_duplicate_roots_and_secret_inside_source_rejected(self):
        config = self.base / "config.toml"
        config.write_text('cookies_file="immich/cookies.json"\nstate_file="state.db"\n'
                          '[[collections]]\nid="a"\nsource="immich"\nremote_root="same"\n'
                          '[[collections]]\nid="b"\nsource="captures"\nremote_root="SAME"\n')
        with self.assertRaises(BackupError):
            load_config(config)
        config.write_text('cookies_file="immich/cookies.json"\nstate_file="state.db"\n'
                          '[[collections]]\nid="a"\nsource="immich"\nremote_root="same"\n')
        with self.assertRaises(BackupError):
            load_config(config)


class ApiTests(unittest.TestCase):
    def test_uk_tls_and_region(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "cookies.json"
            p.write_text(json.dumps({"session-id": "fake", "ubid-acbuk": "fake", "at-acbuk": "fake"}))
            t = Transport("uk", p)
            self.assertEqual(t.web, "www.amazon.co.uk")
            self.assertEqual(t.content, "content-eu.drive.amazonaws.com")
            self.assertTrue(t.context.check_hostname)
            self.assertEqual(t.context.verify_mode, 2)

    def test_missing_auth_does_not_try_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "cookies.json"
            p.write_text("{}")
            with patch("http.client.HTTPSConnection") as connection:
                with self.assertRaises(BackupError):
                    Transport("uk", p)
                connection.assert_not_called()

    def test_root_connect_checks_account_before_write(self):
        class T:
            web = "www.amazon.co.uk"
            def request(self, method, url):
                self.method = method
                return {"data": [{"id": "root", "ownerId": "wrong"}]}
        t = T()
        with self.assertRaises(BackupError):
            Amazon(t).connect("expected")
        self.assertEqual(t.method, "GET")

    def test_incomplete_duplicate_or_huge_listing_rejected(self):
        for page in ({"count": 2, "data": []},
                     {"count": 2, "data": [{"id": "x"}, {"id": "x"}]},
                     {"count": 10000, "data": []}):
            class T:
                web = "www.amazon.co.uk"
                def request(self, *args, **kwargs):
                    return page
            with self.assertRaises(BackupError):
                Amazon(T()).children("parent")

    def test_no_destructive_provider_methods(self):
        for method in ("delete", "trash", "restore", "remove_from_album"):
            self.assertFalse(hasattr(Amazon, method))


if __name__ == "__main__":
    unittest.main()
