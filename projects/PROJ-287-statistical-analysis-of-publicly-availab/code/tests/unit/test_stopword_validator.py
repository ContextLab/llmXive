"""
Unit Tests for Stopword Validator (T014b)
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

import sys
# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.preprocess.stopword_validator import (
    compute_file_hash,
    load_stopword_set,
    validate_determinism,
    validate_window_specificity,
    validate_content_quality,
    run_validation
)


class TestStopwordValidator(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory and mock files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stopwords_dir = Path(self.temp_dir.name)
        
        # Mock Manifest
        self.manifest_data = {
            "windows": [
                {
                    "window": "2000-2004",
                    "filename": "stopwords_2000_2004.json",
                    "hash": "placeholder"
                },
                {
                    "window": "2005-2009",
                    "filename": "stopwords_2005_2009.json",
                    "hash": "placeholder"
                }
            ]
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_file_hash(self):
        """Test SHA256 hash computation."""
        test_file = self.stopwords_dir / "test.txt"
        test_file.write_text("Hello World")
        
        # Calculate expected hash manually
        expected_hash = hashlib.sha256(b"Hello World").hexdigest()
        
        actual_hash = compute_file_hash(test_file)
        self.assertEqual(actual_hash, expected_hash)

    def test_load_stopword_set(self):
        """Test loading stopword set from JSON."""
        data = {"stopwords": ["the", "a", "an"]}
        test_file = self.stopwords_dir / "test.json"
        test_file.write_text(json.dumps(data))
        
        result = load_stopword_set(test_file)
        self.assertEqual(result, {"the", "a", "an"})

    def test_load_stopword_set_missing_key(self):
        """Test error on missing 'stopwords' key."""
        data = {"words": ["the"]}
        test_file = self.stopwords_dir / "bad.json"
        test_file.write_text(json.dumps(data))
        
        with self.assertRaises(ValueError):
            load_stopword_set(test_file)

    @patch('src.data.preprocess.stopword_validator.STOPWORDS_DIR')
    def test_validate_determinism_success(self, mock_stopwords_dir):
        """Test successful determinism validation."""
        mock_stopwords_dir.return_value = self.stopwords_dir
        
        # Create files and calculate hashes
        file1 = self.stopwords_dir / "stopwords_2000_2004.json"
        file1.write_text(json.dumps({"stopwords": ["the", "a"]}))
        hash1 = compute_file_hash(file1)
        
        file2 = self.stopwords_dir / "stopwords_2005_2009.json"
        file2.write_text(json.dumps({"stopwords": ["is", "are"]}))
        hash2 = compute_file_hash(file2)
        
        manifest = {
            "windows": [
                {"window": "2000-2004", "filename": "stopwords_2000_2004.json", "hash": hash1},
                {"window": "2005-2009", "filename": "stopwords_2005_2009.json", "hash": hash2}
            ]
        }
        
        is_valid, errors = validate_determinism(manifest)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    @patch('src.data.preprocess.stopword_validator.STOPWORDS_DIR')
    def test_validate_determinism_hash_mismatch(self, mock_stopwords_dir):
        """Test failure on hash mismatch."""
        mock_stopwords_dir.return_value = self.stopwords_dir
        
        file1 = self.stopwords_dir / "stopwords_2000_2004.json"
        file1.write_text(json.dumps({"stopwords": ["the", "a"]}))
        
        manifest = {
            "windows": [
                {"window": "2000-2004", "filename": "stopwords_2000_2004.json", "hash": "wrong_hash"}
            ]
        }
        
        is_valid, errors = validate_determinism(manifest)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    @patch('src.data.preprocess.stopword_validator.STOPWORDS_DIR')
    def test_validate_window_specificity_distinct(self, mock_stopwords_dir):
        """Test success when lists are distinct."""
        mock_stopwords_dir.return_value = self.stopwords_dir
        
        file1 = self.stopwords_dir / "stopwords_2000_2004.json"
        file1.write_text(json.dumps({"stopwords": ["the", "a", "word1"]}))
        
        file2 = self.stopwords_dir / "stopwords_2005_2009.json"
        file2.write_text(json.dumps({"stopwords": ["the", "a", "word2"]}))
        
        manifest = {
            "windows": [
                {"window": "2000-2004", "filename": "stopwords_2000_2004.json", "hash": "x"},
                {"window": "2005-2009", "filename": "stopwords_2005_2009.json", "hash": "y"}
            ]
        }
        
        is_valid, errors = validate_window_specificity(manifest)
        self.assertTrue(is_valid)

    @patch('src.data.preprocess.stopword_validator.STOPWORDS_DIR')
    def test_validate_window_specificity_identical(self, mock_stopwords_dir):
        """Test failure when lists are identical (global list usage)."""
        mock_stopwords_dir.return_value = self.stopwords_dir
        
        content = json.dumps({"stopwords": ["the", "a", "an"]})
        file1 = self.stopwords_dir / "stopwords_2000_2004.json"
        file1.write_text(content)
        
        file2 = self.stopwords_dir / "stopwords_2005_2009.json"
        file2.write_text(content)
        
        manifest = {
            "windows": [
                {"window": "2000-2004", "filename": "stopwords_2000_2004.json", "hash": "x"},
                {"window": "2005-2009", "filename": "stopwords_2005_2009.json", "hash": "y"}
            ]
        }
        
        is_valid, errors = validate_window_specificity(manifest)
        self.assertFalse(is_valid)
        self.assertTrue(any("identical" in err for err in errors))

    def test_validate_content_quality(self):
        """Test content quality validation."""
        sets = {
            "w1": {"the", "a"},
            "w2": {"is", "are"},
            "w3": set() # Empty set should fail
        }
        
        is_valid, errors = validate_content_quality(sets)
        self.assertFalse(is_valid)
        self.assertTrue(any("empty" in err for err in errors))


if __name__ == "__main__":
    unittest.main()