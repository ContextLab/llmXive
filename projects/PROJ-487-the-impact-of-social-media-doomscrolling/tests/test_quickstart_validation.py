"""
Tests for Quickstart Validation Script
======================================
These tests verify the validation script's logic without running the full pipeline.
"""
import unittest
import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.run_quickstart_validation import (
    run_script,
    check_file_exists,
    validate_artifacts,
    main
)

class TestQuickstartValidation(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        
        # Create mock directory structure
        (self.project_root / "data" / "raw").mkdir(parents=True)
        (self.project_root / "data" / "processed").mkdir(parents=True)
        (self.project_root / "data" / "reports").mkdir(parents=True)
        (self.project_root / "code" / "data").mkdir(parents=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    @patch('subprocess.run')
    def test_run_script_success(self, mock_run):
        """Test successful script execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success",
            stderr=""
        )
        
        script_path = Path("test_script.py")
        success, output = run_script(script_path, args=["--arg1"], timeout=60)
        
        self.assertTrue(success)
        self.assertIn("Success", output)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_script_failure(self, mock_run):
        """Test failed script execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error occurred"
        )
        
        script_path = Path("test_script.py")
        success, output = run_script(script_path, timeout=60)
        
        self.assertFalse(success)
        self.assertIn("Error occurred", output)
    
    def test_check_file_exists_csv(self):
        """Test CSV file existence and row count validation."""
        # Create a valid CSV
        csv_path = Path(self.test_dir) / "test.csv"
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        df.to_csv(csv_path, index=False)
        
        # Test with sufficient rows
        exists, msg = check_file_exists(csv_path, expected_min_rows=3)
        self.assertTrue(exists)
        self.assertIn("OK:", msg)
        
        # Test with insufficient rows
        exists, msg = check_file_exists(csv_path, expected_min_rows=10)
        self.assertFalse(exists)
        self.assertIn("expected >=", msg)
    
    def test_check_file_exists_missing(self):
        """Test missing file detection."""
        missing_path = Path(self.test_dir) / "nonexistent.csv"
        exists, msg = check_file_exists(missing_path)
        
        self.assertFalse(exists)
        self.assertIn("not found", msg)
    
    def test_check_file_exists_json(self):
        """Test JSON file validation."""
        json_path = Path(self.test_dir) / "test.json"
        with open(json_path, 'w') as f:
            json.dump({"key": "value"}, f)
        
        exists, msg = check_file_exists(json_path)
        self.assertTrue(exists)
        self.assertIn("OK", msg)
    
    def test_check_file_exists_pdf(self):
        """Test PDF file validation (non-empty check)."""
        pdf_path = Path(self.test_dir) / "test.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4 fake pdf content")
        
        exists, msg = check_file_exists(pdf_path)
        self.assertTrue(exists)
        self.assertIn("bytes", msg)
    
    def test_empty_pdf_fails(self):
        """Test that empty PDF files are rejected."""
        pdf_path = Path(self.test_dir) / "empty.pdf"
        with open(pdf_path, 'wb') as f:
            pass  # Create empty file
        
        exists, msg = check_file_exists(pdf_path)
        self.assertFalse(exists)
        self.assertIn("empty", msg)
    
    @patch('data.run_quickstart_validation.check_file_exists')
    def test_validate_artifacts(self, mock_check):
        """Test artifact validation logic."""
        # Mock successful checks
        mock_check.return_value = (True, "OK: 100 rows")
        
        # Temporarily override PROJECT_ROOT
        import data.run_quickstart_validation as module
        original_root = module.PROJECT_ROOT
        module.PROJECT_ROOT = Path(self.test_dir)
        
        try:
            results = validate_artifacts()
            self.assertIsInstance(results, dict)
            self.assertGreater(len(results), 0)
        finally:
            module.PROJECT_ROOT = original_root
    
    @patch('data.run_quickstart_validation.run_script')
    @patch('data.run_quickstart_validation.validate_artifacts')
    def test_main_validation_flow(self, mock_validate, mock_run):
        """Test the main validation flow with mocked dependencies."""
        # Mock successful runs
        mock_run.return_value = (True, "Success")
        mock_validate.return_value = {
            "data/raw/gdelt_events.csv": (True, "OK"),
            "data/raw/google_trends.csv": (True, "OK"),
            "data/processed/aligned_timeseries.csv": (True, "OK"),
            "data/processed/stationarity_check.csv": (True, "OK"),
            "data/processed/granger_results.csv": (True, "OK"),
            "data/reports/analysis_report.pdf": (True, "OK"),
        }
        
        # Temporarily override PROJECT_ROOT
        import data.run_quickstart_validation as module
        original_root = module.PROJECT_ROOT
        module.PROJECT_ROOT = Path(self.test_dir)
        
        try:
            # This should not raise an exception
            # Note: We can't easily test sys.exit(0) without catching SystemExit
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 0)
        finally:
            module.PROJECT_ROOT = original_root

if __name__ == "__main__":
    unittest.main()