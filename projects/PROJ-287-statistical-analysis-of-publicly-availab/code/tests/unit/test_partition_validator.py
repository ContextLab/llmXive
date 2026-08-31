"""
Unit tests for partition_validator module.

Tests the validation of non-overlapping multi-year boundaries in processed data files.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.storage.partition_validator import (
    PartitionValidationError,
    extract_year_range_from_filename,
    validate_window_boundaries,
    log_violations_to_manifest,
    run_validation
)


class TestPartitionValidator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processed_dir = Path(self.temp_dir.name) / "processed"
        self.processed_dir.mkdir()
        self.manifest_path = Path(self.temp_dir.name) / "manifest.json"
        
        # Create expected windows structure
        self.expected_windows = [
            (2000, 2004),
            (2005, 2009),
            (2010, 2014),
            (2015, 2019),
            (2020, 2024)
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_extract_year_range_valid(self):
        """Test extraction of year range from valid filenames."""
        test_cases = [
            ("arxiv_processed_2000-2004.csv", (2000, 2004)),
            ("pubmed_processed_2005-2009.csv", (2005, 2009)),
            ("mixed_2010-2014.csv", (2010, 2014)),
        ]
        
        for filename, expected in test_cases:
            result = extract_year_range_from_filename(filename)
            self.assertEqual(result, expected)
    
    def test_extract_year_range_invalid(self):
        """Test extraction from invalid filenames."""
        invalid_cases = [
            "arxiv_processed_2000.csv",  # Missing end year
            "arxiv_processed_2000-2004.txt",  # Wrong extension
            "arxiv_processed_20002004.csv",  # Missing dash
            "invalid_name.csv",  # No years
        ]
        
        for filename in invalid_cases:
            result = extract_year_range_from_filename(filename)
            self.assertIsNone(result)
    
    def test_validate_no_files(self):
        """Test validation with no CSV files."""
        is_valid, violations = validate_window_boundaries(self.processed_dir, {})
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)
    
    def test_validate_all_windows_present(self):
        """Test validation with all expected windows present."""
        # Create CSV files for all expected windows
        for start, end in self.expected_windows:
            filename = f"arxiv_processed_{start}-{end}.csv"
            (self.processed_dir / filename).touch()
        
        is_valid, violations = validate_window_boundaries(self.processed_dir, {})
        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)
    
    def test_validate_missing_windows(self):
        """Test validation with missing expected windows."""
        # Create only some windows
        partial_windows = self.expected_windows[:3]
        for start, end in partial_windows:
            filename = f"arxiv_processed_{start}-{end}.csv"
            (self.processed_dir / filename).touch()
        
        is_valid, violations = validate_window_boundaries(self.processed_dir, {})
        self.assertFalse(is_valid)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["violation_type"], "missing_windows")
    
    def test_validate_invalid_naming(self):
        """Test validation with invalid filename patterns."""
        invalid_files = [
            "arxiv_processed_2000.csv",
            "arxiv_processed_2000-2004.txt",
            "invalid_name.csv"
        ]
        
        for filename in invalid_files:
            (self.processed_dir / filename).touch()
        
        is_valid, violations = validate_window_boundaries(self.processed_dir, {})
        self.assertFalse(is_valid)
        # Should have violations for each invalid file
        invalid_violations = [v for v in violations if v["violation_type"] == "invalid_naming"]
        self.assertGreater(len(invalid_violations), 0)
    
    def test_validate_unexpected_window(self):
        """Test validation with unexpected year ranges."""
        # Create a file with an unexpected window
        filename = "arxiv_processed_1995-1999.csv"
        (self.processed_dir / filename).touch()
        
        is_valid, violations = validate_window_boundaries(self.processed_dir, {})
        self.assertFalse(is_valid)
        unexpected_violations = [v for v in violations if v["violation_type"] == "unexpected_window"]
        self.assertEqual(len(unexpected_violations), 1)
    
    def test_validate_duplicate_window(self):
        """Test validation with duplicate windows."""
        # Create duplicate windows
        for i in range(2):
            filename = f"arxiv_processed_2000-2004_{i}.csv"
            (self.processed_dir / filename).touch()
        
        # Note: Our current implementation only checks exact matches in expected windows
        # This test verifies the behavior with slightly different filenames
        is_valid, violations = validate_window_boundaries(self.processed_dir, {})
        # The second file will be flagged as invalid naming or unexpected window
        # depending on the exact filename pattern
        self.assertFalse(is_valid)
    
    def test_log_violations_to_manifest(self):
        """Test logging violations to manifest."""
        violations = [
            {
                "file": "test.csv",
                "violation_type": "invalid_naming",
                "details": "Test violation"
            }
        ]
        
        log_violations_to_manifest(violations, self.manifest_path, False)
        
        self.assertTrue(self.manifest_path.exists())
        with open(self.manifest_path, 'r') as f:
            manifest = json.load(f)
        
        self.assertIn("partition_validation", manifest)
        self.assertFalse(manifest["partition_validation"]["passed"])
        self.assertEqual(len(manifest["partition_validation"]["violations"]), 1)
    
    def test_run_validation_success(self):
        """Test successful validation run."""
        # Create all expected windows
        for start, end in self.expected_windows:
            filename = f"arxiv_processed_{start}-{end}.csv"
            (self.processed_dir / filename).touch()
        
        success = run_validation(self.processed_dir, self.manifest_path)
        self.assertTrue(success)
        self.assertTrue(self.manifest_path.exists())
    
    def test_run_validation_failure(self):
        """Test failed validation run."""
        # Create incomplete windows
        for start, end in self.expected_windows[:3]:
            filename = f"arxiv_processed_{start}-{end}.csv"
            (self.processed_dir / filename).touch()
        
        success = run_validation(self.processed_dir, self.manifest_path)
        self.assertFalse(success)
        self.assertTrue(self.manifest_path.exists())
    
    @patch('src.data.storage.partition_validator.get_logger')
    def test_run_validation_exception(self, mock_logger):
        """Test validation with directory that doesn't exist."""
        nonexistent_dir = Path("/nonexistent/directory")
        
        # Should handle missing directory gracefully
        success = run_validation(nonexistent_dir, self.manifest_path)
        self.assertTrue(success)  # No files = no violations


if __name__ == "__main__":
    unittest.main()