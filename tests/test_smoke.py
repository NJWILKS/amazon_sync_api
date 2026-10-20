import unittest
from unittest.mock import Mock
from amazon_sync_api.core import BackupError
from amazon_sync_api.smoke import create_test_folder


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
        p.ensure_folder.assert_called_once_with("root", "integration-test-amazon-sync-api")
        p.find.assert_called_once_with("root", "integration-test-amazon-sync-api", "FOLDER")

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
