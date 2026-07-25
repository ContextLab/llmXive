"""
Tests for formatting utilities and T039 verification.
"""

import unittest
import os
import json
from pathlib import Path

class TestFormatting(unittest.TestCase):
    """Test cases for formatting operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.code_dir = self.project_root / "code"
        self.results_dir = self.project_root / "data" / "results"
    
    def test_formatting_report_exists(self):
        """Verify that the formatting report was generated."""
        report_path = self.results_dir / "formatting_report.json"
        self.assertTrue(
            report_path.exists(),
            f"Formatting report not found at {report_path}"
        )
    
    def test_formatting_report_structure(self):
        """Verify the formatting report has the expected structure."""
        report_path = self.results_dir / "formatting_report.json"
        
        if not report_path.exists():
            self.skipTest("Report file not found")
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn("task_id", report)
        self.assertEqual(report["task_id"], "T039")
        self.assertIn("steps", report)
        self.assertIsInstance(report["steps"], list)
    
    def test_ruff_config_exists(self):
        """Verify ruff configuration file exists."""
        ruff_config = self.code_dir / ".ruff.toml"
        self.assertTrue(
            ruff_config.exists(),
            f"Ruff config not found at {ruff_config}"
        )
    
    def test_black_config_exists(self):
        """Verify black configuration file exists."""
        black_config = self.code_dir / ".black.toml"
        self.assertTrue(
            black_config.exists(),
            f"Black config not found at {black_config}"
        )
    
    def test_formatting_script_exists(self):
        """Verify the formatting script exists."""
        script_path = self.code_dir / "run_formatting.py"
        self.assertTrue(
            script_path.exists(),
            f"Formatting script not found at {script_path}"
        )

if __name__ == "__main__":
    unittest.main()