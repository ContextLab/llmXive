"""
Unit tests for the SQLite metadata registry schema and helper functions.
"""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

# Adjust import path to match project structure
from code.utils.db_schema import init_db, ensure_subject, register_file, update_file_status, get_files_by_status


class TestMetadataRegistry(unittest.TestCase):
    def setUp(self):
        """Create a temporary database for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_registry.db")
        self.conn = init_db(self.db_path)

    def tearDown(self):
        """Clean up the temporary database."""
        self.conn.close()
        self.temp_dir.cleanup()

    def test_schema_creation(self):
        """Verify that tables are created upon initialization."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        self.assertIn("subjects", tables)
        self.assertIn("files", tables)

    def test_ensure_subject(self):
        """Test that a subject can be added to the registry."""
        ensure_subject(self.conn, "sub-001")
        cursor = self.conn.cursor()
        cursor.execute("SELECT subject_id, status FROM subjects WHERE subject_id = ?", ("sub-001",))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["subject_id"], "sub-001")
        self.assertEqual(row["status"], "pending")

    def test_ensure_subject_idempotent(self):
        """Ensure that calling ensure_subject twice doesn't duplicate rows."""
        ensure_subject(self.conn, "sub-001")
        ensure_subject(self.conn, "sub-001")
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM subjects WHERE subject_id = ?", ("sub-001",))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

    def test_register_file(self):
        """Test registering a file associated with a subject."""
        register_file(self.conn, "sub-001", "data/raw/sub-001/task-rest_bold.nii.gz", checksum="abc123")
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT subject_id, file_path, checksum, status FROM files WHERE subject_id = ?",
            ("sub-001",)
        )
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["file_path"], "data/raw/sub-001/task-rest_bold.nii.gz")
        self.assertEqual(row["checksum"], "abc123")
        self.assertEqual(row["status"], "pending")

    def test_update_file_status(self):
        """Test updating the status and checksum of a file."""
        register_file(self.conn, "sub-002", "data/raw/sub-002/task-rest_bold.nii.gz", checksum="old_hash")
        update_file_status(self.conn, "sub-002", "data/raw/sub-002/task-rest_bold.nii.gz", "processed", checksum="new_hash")

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT status, checksum FROM files WHERE subject_id = ? AND file_path = ?",
            ("sub-002", "data/raw/sub-002/task-rest_bold.nii.gz")
        )
        row = cursor.fetchone()
        self.assertEqual(row["status"], "processed")
        self.assertEqual(row["checksum"], "new_hash")

    def test_get_files_by_status(self):
        """Test retrieving files by their status."""
        register_file(self.conn, "sub-003", "data/raw/sub-003/task-rest_bold.nii.gz", status="pending")
        register_file(self.conn, "sub-004", "data/raw/sub-004/task-rest_bold.nii.gz", status="processed")

        pending_files = get_files_by_status(self.conn, "pending")
        processed_files = get_files_by_status(self.conn, "processed")

        self.assertEqual(len(pending_files), 1)
        self.assertEqual(len(processed_files), 1)
        self.assertEqual(pending_files[0]["subject_id"], "sub-003")
        self.assertEqual(processed_files[0]["subject_id"], "sub-004")


if __name__ == "__main__":
    unittest.main()
