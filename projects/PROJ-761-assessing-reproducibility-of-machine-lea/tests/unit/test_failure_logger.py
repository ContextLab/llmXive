"""
Unit tests for the failure_logger module (T030).
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
# Assuming the module is in code/failure_logger.py
import sys
sys.path.insert(0, 'code')
from failure_logger import (
    record_failure,
    load_existing_failure_log,
    compile_failure_summary,
    FailureReason,
    write_failure_report
)

class TestFailureLogger(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test logs."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_path = os.path.join(self.temp_dir, "test_failures.json")
        self.test_report_path = os.path.join(self.temp_dir, "test_summary.json")

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)
        if os.path.exists(self.test_report_path):
            os.remove(self.test_report_path)
        os.rmdir(self.temp_dir)

    def test_record_failure_creates_file(self):
        """Test that recording a failure creates the log file."""
        record_failure(
            paper_id="10.1234/test",
            reason=FailureReason.DATA_GAPS,
            details="Test failure",
            log_path=self.test_log_path
        )
        self.assertTrue(os.path.exists(self.test_log_path))

    def test_record_failure_appends(self):
        """Test that multiple failures are appended to the log."""
        record_failure("10.1234/a", FailureReason.DATA_GAPS, "Fail A", log_path=self.test_log_path)
        record_failure("10.1234/b", FailureReason.MODEL_SUBSTITUTION, "Fail B", log_path=self.test_log_path)
        
        data = load_existing_failure_log(self.test_log_path)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["paper_id"], "10.1234/a")
        self.assertEqual(data[1]["paper_id"], "10.1234/b")

    def test_load_existing_failure_log_empty(self):
        """Test loading from a non-existent file returns empty list."""
        data = load_existing_failure_log(self.test_log_path)
        self.assertEqual(data, [])

    def test_compile_failure_summary(self):
        """Test the compilation of failure summaries."""
        record_failure("10.1234/a", FailureReason.DATA_GAPS, "Fail A", log_path=self.test_log_path)
        record_failure("10.1234/b", FailureReason.DATA_GAPS, "Fail B", log_path=self.test_log_path)
        record_failure("10.1234/c", FailureReason.MODEL_SUBSTITUTION, "Fail C", log_path=self.test_log_path)
        
        summary = compile_failure_summary(self.test_log_path)
        
        self.assertEqual(summary["total_failures"], 3)
        self.assertEqual(summary["by_reason"]["data_gaps"], 2)
        self.assertEqual(summary["by_reason"]["model_substitution"], 1)
        self.assertEqual(len(summary["by_paper"]), 3)

    def test_write_failure_report(self):
        """Test writing the summary report to disk."""
        record_failure("10.1234/a", FailureReason.DATA_GAPS, "Fail A", log_path=self.test_log_path)
        
        write_failure_report(self.test_report_path)
        
        self.assertTrue(os.path.exists(self.test_report_path))
        with open(self.test_report_path, 'r') as f:
            data = json.load(f)
            self.assertIn("total_failures", data)
            self.assertEqual(data["total_failures"], 1)

    def test_record_failure_missing_fields(self):
        """Test that missing paper_id or reason raises ValueError."""
        with self.assertRaises(ValueError):
            record_failure(paper_id="", reason=FailureReason.DATA_GAPS, details="Test")
        
        with self.assertRaises(ValueError):
            record_failure(paper_id="10.1234", reason="", details="Test")

if __name__ == '__main__':
    unittest.main()