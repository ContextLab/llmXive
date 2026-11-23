"""
Unit tests for verify_artifact_distinction.py script.
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest import TestCase, main as unittest_main
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.verify_artifact_distinction import (
    get_file_checksum,
    get_raw_files,
    get_processed_files,
    verify_artifact_distinction
)


class TestGetRawFiles(TestCase):
    """Tests for get_raw_files function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_raw_files_with_csv_files(self):
        """Test that raw CSV files are correctly identified."""
        # Create test files
        (self.data_raw_dir / "adult_raw.csv").touch()
        (self.data_raw_dir / "compas_raw.csv").touch()
        (self.data_raw_dir / "other.txt").touch()  # Should be ignored

        raw_files = get_raw_files(self.data_raw_dir)
        
        self.assertEqual(len(raw_files), 2)
        names = [name for name, _ in raw_files]
        self.assertIn("adult", names)
        self.assertIn("compas", names)

    def test_get_raw_files_empty_directory(self):
        """Test that empty directory returns empty list."""
        raw_files = get_raw_files(self.data_raw_dir)
        self.assertEqual(raw_files, [])

    def test_get_raw_files_nonexistent_directory(self):
        """Test that nonexistent directory returns empty list."""
        raw_files = get_raw_files(Path("/nonexistent/path"))
        self.assertEqual(raw_files, [])


class TestGetProcessedFiles(TestCase):
    """Tests for get_processed_files function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_processed_dir = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_processed_files_with_csv_files(self):
        """Test that processed CSV files are correctly identified."""
        # Create test files
        (self.data_processed_dir / "adult_processed.csv").touch()
        (self.data_processed_dir / "compas_processed.csv").touch()
        (self.data_processed_dir / "other.txt").touch()  # Should be ignored

        processed_files = get_processed_files(self.data_processed_dir)
        
        self.assertEqual(len(processed_files), 2)
        names = [name for name, _ in processed_files]
        self.assertIn("adult", names)
        self.assertIn("compas", names)

    def test_get_processed_files_empty_directory(self):
        """Test that empty directory returns empty list."""
        processed_files = get_processed_files(self.data_processed_dir)
        self.assertEqual(processed_files, [])


class TestVerifyArtifactDistinction(TestCase):
    """Tests for verify_artifact_distinction function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_path = Path(self.temp_dir) / "state.yaml"
        self.data_raw_dir = Path(self.temp_dir) / "raw"
        self.data_processed_dir = Path(self.temp_dir) / "processed"
        self.output_path = Path(self.temp_dir) / "output.json"

        self.data_raw_dir.mkdir()
        self.data_processed_dir.mkdir()

        # Create test files with different content
        self.raw_file = self.data_raw_dir / "adult_raw.csv"
        self.proc_file = self.data_processed_dir / "adult_processed.csv"

        self.raw_file.write_text("raw_data_content")
        self.proc_file.write_text("processed_data_content")

        # Create state file with checksums
        raw_checksum = hashlib.sha256(b"raw_data_content").hexdigest()
        proc_checksum = hashlib.sha256(b"processed_data_content").hexdigest()

        state_content = {
            "artifact_hashes": {
                "raw": {"adult_raw.csv": raw_checksum},
                "processed": {"adult_processed.csv": proc_checksum}
            }
        }

        import yaml
        with open(self.state_path, "w") as f:
            yaml.dump(state_content, f)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_distinct_artifacts_pass(self):
        """Test that distinct raw and processed files pass verification."""
        results = verify_artifact_distinction(
            state_path=self.state_path,
            data_raw_dir=self.data_raw_dir,
            data_processed_dir=self.data_processed_dir,
            output_path=self.output_path
        )

        self.assertEqual(results["verification_status"], "passed")
        self.assertEqual(len(results["artifacts"]), 1)
        self.assertEqual(results["artifacts"][0]["status"], "passed")
        self.assertTrue(results["artifacts"][0]["path_distinct"])
        self.assertTrue(results["artifacts"][0]["checksum_distinct"])

    def test_same_checksum_fails(self):
        """Test that identical checksums cause verification to fail."""
        # Make processed file have same content as raw
        self.proc_file.write_text("raw_data_content")
        
        # Update state with same checksum
        raw_checksum = hashlib.sha256(b"raw_data_content").hexdigest()
        state_content = {
            "artifact_hashes": {
                "raw": {"adult_raw.csv": raw_checksum},
                "processed": {"adult_processed.csv": raw_checksum}
            }
        }

        import yaml
        with open(self.state_path, "w") as f:
            yaml.dump(state_content, f)

        results = verify_artifact_distinction(
            state_path=self.state_path,
            data_raw_dir=self.data_raw_dir,
            data_processed_dir=self.data_processed_dir,
            output_path=self.output_path
        )

        self.assertEqual(results["verification_status"], "failed")
        self.assertEqual(len(results["artifacts"]), 1)
        self.assertEqual(results["artifacts"][0]["status"], "failed")
        self.assertFalse(results["artifacts"][0]["checksum_distinct"])

    def test_missing_raw_file_warning(self):
        """Test that missing raw file generates warning."""
        # Remove raw file
        self.raw_file.unlink()

        results = verify_artifact_distinction(
            state_path=self.state_path,
            data_raw_dir=self.data_raw_dir,
            data_processed_dir=self.data_processed_dir,
            output_path=self.output_path
        )

        self.assertEqual(results["verification_status"], "warning")
        self.assertEqual(len(results["artifacts"]), 1)
        self.assertEqual(results["artifacts"][0]["status"], "warning")

    def test_output_file_created(self):
        """Test that output JSON file is created."""
        results = verify_artifact_distinction(
            state_path=self.state_path,
            data_raw_dir=self.data_raw_dir,
            data_processed_dir=self.data_processed_dir,
            output_path=self.output_path
        )

        self.assertTrue(self.output_path.exists())
        
        with open(self.output_path, "r") as f:
            output_data = json.load(f)
        
        self.assertIn("verification_status", output_data)
        self.assertIn("artifacts", output_data)
        self.assertIn("timestamp", output_data)


if __name__ == "__main__":
    unittest_main()