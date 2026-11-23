"""
Unit tests for stopword validator module.
"""
import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.preprocess.stopword_validator import (
    load_manifest,
    compute_file_hash,
    load_stopword_set,
    validate_determinism,
    validate_window_specificity,
    validate_content_quality,
    run_validation
)


class TestStopwordValidator(unittest.TestCase):
    """Test cases for stopword validator functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stopword_dir = Path(self.temp_dir.name) / "stopwords"
        self.stopword_dir.mkdir(parents=True)

        # Create sample stopword files
        self.window1_path = self.stopword_dir / "window_2000_2004.json"
        self.window2_path = self.stopword_dir / "window_2005_2009.json"

        with open(self.window1_path, 'w') as f:
            json.dump({"stopwords": ["the", "and", "of", "to", "a"]}, f)

        with open(self.window2_path, 'w') as f:
            json.dump({"stopwords": ["the", "and", "of", "to", "in", "for"]}, f)

        # Create manifest
        self.manifest_path = self.stopword_dir / "manifest.json"
        self.manifest_data = {
            "windows": {
                "2000-2004": {
                    "file_path": str(self.window1_path),
                    "hash": "placeholder"
                },
                "2005-2009": {
                    "file_path": str(self.window2_path),
                    "hash": "placeholder"
                }
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_manifest_success(self):
        """Test loading a valid manifest."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        self.assertIn("windows", manifest)
        self.assertEqual(len(manifest["windows"]), 2)

    def test_load_manifest_not_found(self):
        """Test loading a non-existent manifest raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_manifest(Path("/nonexistent/path/manifest.json"))

    def test_compute_file_hash(self):
        """Test file hash computation is deterministic."""
        hash1 = compute_file_hash(self.window1_path)
        hash2 = compute_file_hash(self.window1_path)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex length

    def test_load_stopword_set(self):
        """Test loading stopwords from JSON file."""
        stopwords = load_stopword_set(self.window1_path)
        self.assertIsInstance(stopwords, set)
        self.assertIn("the", stopwords)
        self.assertEqual(len(stopwords), 5)

    def test_validate_determinism_success(self):
        """Test determinism validation with correct hashes."""
        # Update manifest with correct hashes
        hash1 = compute_file_hash(self.window1_path)
        hash2 = compute_file_hash(self.window2_path)

        self.manifest_data["windows"]["2000-2004"]["hash"] = hash1
        self.manifest_data["windows"]["2005-2009"]["hash"] = hash2

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        is_valid, errors = validate_determinism(manifest)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_determinism_hash_mismatch(self):
        """Test determinism validation fails on hash mismatch."""
        self.manifest_data["windows"]["2000-2004"]["hash"] = "wrong_hash"

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        is_valid, errors = validate_determinism(manifest)

        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Hash mismatch" in err for err in errors))

    def test_validate_window_specificity_success(self):
        """Test window specificity validation with different lists."""
        self.manifest_data["windows"]["2000-2004"]["hash"] = compute_file_hash(self.window1_path)
        self.manifest_data["windows"]["2005-2009"]["hash"] = compute_file_hash(self.window2_path)

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        is_valid, errors = validate_window_specificity(manifest)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_window_specificity_identical_lists(self):
        """Test window specificity fails when lists are identical."""
        # Make both windows have identical content
        with open(self.window2_path, 'w') as f:
            json.dump({"stopwords": ["the", "and", "of", "to", "a"]}, f)

        self.manifest_data["windows"]["2000-2004"]["hash"] = compute_file_hash(self.window1_path)
        self.manifest_data["windows"]["2005-2009"]["hash"] = compute_file_hash(self.window2_path)

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        is_valid, errors = validate_window_specificity(manifest)

        self.assertFalse(is_valid)
        self.assertTrue(any("IDENTICAL" in err for err in errors))

    def test_validate_content_quality_success(self):
        """Test content quality validation with valid lists."""
        self.manifest_data["windows"]["2000-2004"]["hash"] = compute_file_hash(self.window1_path)
        self.manifest_data["windows"]["2005-2009"]["hash"] = compute_file_hash(self.window2_path)

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        is_valid, errors = validate_content_quality(manifest)

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_content_quality_too_few_words(self):
        """Test content quality fails with too few stopwords."""
        # Create a file with too few stopwords
        small_path = self.stopword_dir / "small.json"
        with open(small_path, 'w') as f:
            json.dump({"stopwords": ["the"]}, f)

        self.manifest_data["windows"]["2000-2004"]["file_path"] = str(small_path)
        self.manifest_data["windows"]["2000-2004"]["hash"] = compute_file_hash(small_path)

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        manifest = load_manifest(self.manifest_path)
        is_valid, errors = validate_content_quality(manifest)

        self.assertFalse(is_valid)
        self.assertTrue(any("too few" in err for err in errors))

    def test_run_validation_complete(self):
        """Test complete validation run."""
        self.manifest_data["windows"]["2000-2004"]["hash"] = compute_file_hash(self.window1_path)
        self.manifest_data["windows"]["2005-2009"]["hash"] = compute_file_hash(self.window2_path)

        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest_data, f)

        result = run_validation(self.manifest_path)

        self.assertIn("overall_pass", result)
        self.assertIn("determinism", result)
        self.assertIn("window_specificity", result)
        self.assertIn("content_quality", result)
        self.assertIn("total_errors", result)

        self.assertTrue(result["overall_pass"])
        self.assertEqual(result["total_errors"], 0)


if __name__ == "__main__":
    unittest.main()