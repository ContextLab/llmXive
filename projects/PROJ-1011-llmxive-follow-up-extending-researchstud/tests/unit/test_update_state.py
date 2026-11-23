"""
Unit tests for the state management utility (update_state.py).

Tests cover:
- Artifact registration and metadata calculation
- Version tracking and snapshots
- Integrity verification
- Error handling for missing files
"""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch, MagicMock
import datetime

# Import the module under test
# We need to handle the relative import properly in tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.update_state import (
    ensure_state_dir,
    get_current_version,
    set_version,
    get_artifact_metadata,
    update_state_for_artifact,
    get_artifact_state,
    verify_artifact_integrity,
    record_version_snapshot,
    STATE_DIR,
    VERSION_FILE,
    MANIFEST_PATH,
)
from utils.data_manifest import load_manifest, save_manifest


class TestUpdateState(TestCase):
    """Test cases for state management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Ensure state directory exists
        ensure_state_dir()

        # Clean manifest for each test
        if MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ensure_state_dir_creates_directory(self):
        """Test that ensure_state_dir creates the state directory."""
        temp_state = tempfile.mkdtemp()
        try:
            with patch("utils.update_state.STATE_DIR", Path(temp_state)):
                result = ensure_state_dir()
                self.assertTrue(result.exists())
        finally:
            shutil.rmtree(temp_state, ignore_errors=True)

    def test_get_current_version_default(self):
        """Test that get_current_version returns default when no version file exists."""
        if VERSION_FILE.exists():
            VERSION_FILE.unlink()

        version = get_current_version()
        self.assertEqual(version, "0.0.0")

    def test_get_current_version_from_file(self):
        """Test that get_current_version reads from version file."""
        VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        VERSION_FILE.write_text("1.2.3")

        version = get_current_version()
        self.assertEqual(version, "1.2.3")

    def test_set_version_writes_file(self):
        """Test that set_version writes to the version file."""
        set_version("2.0.0")

        self.assertTrue(VERSION_FILE.exists())
        self.assertEqual(VERSION_FILE.read_text(), "2.0.0")

    def test_get_artifact_metadata(self):
        """Test metadata calculation for an artifact file."""
        # Create a test file
        test_file = Path("test_artifact.txt")
        test_content = "Test content for artifact metadata"
        test_file.write_text(test_content)

        metadata = get_artifact_metadata(test_file)

        self.assertIn("path", metadata)
        self.assertIn("checksum", metadata)
        self.assertIn("size_bytes", metadata)
        self.assertIn("created_at", metadata)
        self.assertIn("modified_at", metadata)
        self.assertEqual(metadata["size_bytes"], len(test_content))

    def test_get_artifact_metadata_missing_file(self):
        """Test that get_artifact_metadata raises FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            get_artifact_metadata("nonexistent_file.txt")

    def test_update_state_for_artifact(self):
        """Test updating state for a new artifact."""
        test_file = Path("data/test_output.json")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"key": "value"}')

        entry = update_state_for_artifact(
            test_file,
            "T006",
            "Test artifact for state management",
            dependencies=["T001a", "T004"],
        )

        self.assertEqual(entry["task_id"], "T006")
        self.assertEqual(entry["description"], "Test artifact for state management")
        self.assertEqual(entry["dependencies"], ["T001a", "T004"])
        self.assertIn("metadata", entry)
        self.assertEqual(entry["metadata"]["path"], str(test_file))

        # Verify manifest was updated
        manifest = load_manifest()
        self.assertIn(str(test_file), manifest["artifacts"])

    def test_update_state_for_artifact_missing_file(self):
        """Test that update_state_for_artifact raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            update_state_for_artifact(
                "nonexistent.txt",
                "T006",
                "Test",
            )

    def test_get_artifact_state(self):
        """Test retrieving artifact state."""
        test_file = Path("data/test_output.json")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"key": "value"}')

        update_state_for_artifact(test_file, "T006", "Test artifact")

        state = get_artifact_state(test_file)

        self.assertIsNotNone(state)
        self.assertEqual(state["task_id"], "T006")

    def test_get_artifact_state_missing(self):
        """Test that get_artifact_state returns None for missing artifact."""
        state = get_artifact_state("nonexistent.txt")
        self.assertIsNone(state)

    def test_verify_artifact_integrity(self):
        """Test integrity verification for valid artifact."""
        test_file = Path("data/test_output.json")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"key": "value"}')

        update_state_for_artifact(test_file, "T006", "Test artifact")

        self.assertTrue(verify_artifact_integrity(test_file))

    def test_verify_artifact_integrity_modified(self):
        """Test integrity verification fails for modified artifact."""
        test_file = Path("data/test_output.json")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"key": "value"}')

        update_state_for_artifact(test_file, "T006", "Test artifact")

        # Modify the file
        test_file.write_text('{"key": "modified"}')

        self.assertFalse(verify_artifact_integrity(test_file))

    def test_verify_artifact_integrity_missing(self):
        """Test integrity verification returns False for missing artifact."""
        self.assertFalse(verify_artifact_integrity("nonexistent.txt"))

    def test_record_version_snapshot(self):
        """Test recording a version snapshot."""
        # Create a test artifact first
        test_file = Path("data/test_output.json")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"key": "value"}')
        update_state_for_artifact(test_file, "T006", "Test artifact")

        version = record_version_snapshot("T006", "Initial snapshot")

        self.assertTrue(version.startswith("v"))
        self.assertTrue(len(version) > 2)  # v + timestamp

        manifest = load_manifest()
        self.assertIn("version_history", manifest)
        self.assertEqual(len(manifest["version_history"]), 1)
        self.assertEqual(manifest["version_history"][0]["task_id"], "T006")
        self.assertEqual(manifest["version_history"][0]["description"], "Initial snapshot")

    def test_record_version_snapshot_updates_current(self):
        """Test that record_version_snapshot updates the current version."""
        record_version_snapshot("T006", "Test snapshot")

        manifest = load_manifest()
        version_file_content = VERSION_FILE.read_text()

        self.assertEqual(manifest["current_version"], version_file_content)


if __name__ == "__main__":
    unittest_main()