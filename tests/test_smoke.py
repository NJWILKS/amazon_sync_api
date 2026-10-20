import unittest
import hashlib
from pathlib import Path
import tempfile
from unittest.mock import Mock
from amazon_sync_api.core import BackupError
from amazon_sync_api.smoke import create_test_folder, verify_image, sample_png


class SmokeTests(unittest.TestCase):
    def provider(self, data):
        p = Mock()
        p.base = "https://www.amazon.co.uk/drive/v1"
        p.transport.request.return_value = {"data": data}
        p.ensure_folder.return_value = "folder"
        p.find.return_value = "folder"
        return p

    def test_discovers_account_creates_and_reads_test_folder(self):
        p = self.provider([{"id": "root", "ownerId": "owner"}])
        create_test_folder(p)
        p.transport.request.assert_called_once()
        self.assertEqual(p.transport.request.call_args.args[0], "GET")
        p.ensure_folder.assert_called_once_with("root", "test")
        p.find.assert_called_once_with("root", "test", "FOLDER")

    def test_invalid_root_never_creates_folder(self):
        for rows in ([], [{"id": "root"}], [{"id": "a", "ownerId": "b"}]*2):
            p = self.provider(rows)
            with self.assertRaises(BackupError):
                create_test_folder(p)
            p.ensure_folder.assert_not_called()

    def test_read_back_mismatch_fails(self):
        p = self.provider([{"id": "root", "ownerId": "owner"}])
        p.find.return_value = "different"
        with self.assertRaises(BackupError):
            create_test_folder(p)

    def image_provider(self):
        p = self.provider([{"id": "root", "ownerId": "owner"}])
        p.ensure_folder.side_effect = ["test-root", "timestamp-folder"]
        p.find.side_effect = ["test-root", None, "timestamp-folder"]
        p.upload.return_value = "image"
        p.find_file.return_value = "image"
        p.original_sha256.return_value = hashlib.sha256(sample_png()).hexdigest()
        return p

    def test_timestamp_tree_and_original_hash(self):
        p = self.image_provider()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            result = verify_image(p, path, "20261020140000")
            self.assertEqual(result, "test/20261020140000/sample.png")
            p.upload.assert_called_once_with("timestamp-folder", "sample.png", path / "sample.png")
            p.original_sha256.assert_called_once_with("image")

    def test_corrupted_original_fails(self):
        p = self.image_provider()
        p.original_sha256.return_value = "wrong"
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(BackupError):
            verify_image(p, Path(tmp), "20261020140000")

    def test_timestamp_collision_never_uploads(self):
        p = self.image_provider()
        p.find.side_effect = ["test-root", "existing"]
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(BackupError):
            verify_image(p, Path(tmp), "20261020140000")
        p.upload.assert_not_called()
