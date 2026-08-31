import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.quickstart_validator import (
    compute_file_hash,
    check_directory_exists,
    validate_artifact,
    run_quickstart_validation,
    generate_checksum_manifest
)

class TestQuickstartValidator(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.txt"
        self.test_file.write_text("Hello World")
        self.test_dir = self.temp_dir / "subdir"
        self.test_dir.mkdir()
        (self.test_dir / "nested.txt").write_text("Nested")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_compute_file_hash(self):
        """Test SHA-256 hash computation."""
        expected_hash = "d2a84f4b8b650937ec8f73cd8be2c74add5a911ba64df27458ed8229da804a26"
        actual_hash = compute_file_hash(self.test_file)
        self.assertEqual(actual_hash, expected_hash)

    def test_compute_file_hash_missing(self):
        """Test hash computation on missing file."""
        missing_file = self.temp_dir / "missing.txt"
        hash_val = compute_file_hash(missing_file)
        self.assertEqual(hash_val, "ERROR")

    def test_check_directory_exists(self):
        """Test directory existence and non-empty check."""
        self.assertTrue(check_directory_exists(self.test_dir))
        self.assertFalse(check_directory_exists(self.temp_dir / "nonexistent"))
        
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()
        self.assertFalse(check_directory_exists(empty_dir))

    def test_validate_artifact_file(self):
        """Test validation of a file artifact."""
        # Mock project_root to be temp_dir
        with patch('utils.quickstart_validator.project_root', self.temp_dir):
            result = validate_artifact("test.txt", "CI")
            self.assertTrue(result["exists"])
            self.assertTrue(result["valid"])
            self.assertIsNotNone(result["hash"])
            self.assertIn("sha256", result["message"].lower() or "hash" in result["message"].lower())

    def test_validate_artifact_directory(self):
        """Test validation of a directory artifact."""
        with patch('utils.quickstart_validator.project_root', self.temp_dir):
            result = validate_artifact("subdir", "CI")
            self.assertTrue(result["exists"])
            self.assertTrue(result["valid"])

    def test_validate_artifact_missing(self):
        """Test validation of a missing artifact."""
        with patch('utils.quickstart_validator.project_root', self.temp_dir):
            result = validate_artifact("missing.txt", "CI")
            self.assertFalse(result["exists"])
            self.assertFalse(result["valid"])
            self.assertEqual(result["message"], "File not found")

    def test_validate_artifact_optional_research(self):
        """Test optional artifact logic in CI mode."""
        with patch('utils.quickstart_validator.project_root', self.temp_dir):
            # Simulate human_scores.csv which is optional in CI
            result = validate_artifact("data/annotations/human_scores.csv", "CI")
            # Since it doesn't exist, it should be marked as skipped/valid for CI
            self.assertTrue(result["valid"])
            self.assertIn("Optional in CI", result["message"])

    def test_generate_checksum_manifest(self):
        """Test manifest generation."""
        mock_results = {
            "mode": "CI",
            "artifacts": {
                "data_processed": [
                    {"path": "data/processed/masked_images", "hash": "abc123", "valid": True}
                ]
            },
            "summary": {"overall_status": "PASSED"}
        }
        output_path = self.temp_dir / "manifest.json"
        generate_checksum_manifest(mock_results, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path) as f:
            data = json.load(f)
        self.assertEqual(data["mode"], "CI")
        self.assertEqual(data["overall_status"], "PASSED")
        self.assertEqual(len(data["files"]), 1)

    @patch('utils.quickstart_validator.logger')
    def test_run_quickstart_validation_ci_mode(self, mock_logger):
        """Test full validation run in CI mode."""
        # Create a minimal mock structure
        mock_mode = "CI"
        # We can't easily mock the full REQUIRED_ARTIFACTS without breaking imports,
        # so we test that the function returns a structured dict
        with patch('utils.quickstart_validator.REQUIRED_ARTIFACTS', {
            "test": ["test.txt"]
        }):
            with patch('utils.quickstart_validator.project_root', self.temp_dir):
                results = run_quickstart_validation(mock_mode)
                self.assertIn("artifacts", results)
                self.assertIn("summary", results)
                self.assertEqual(results["mode"], mock_mode)

if __name__ == "__main__":
    unittest.main()