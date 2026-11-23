"""
Tests for Task T039: Linting and Formatting.
"""
import os
import unittest
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

class TestTaskT039(unittest.TestCase):
    """Test cases for the T039 linting task."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.code_dir = self.project_root / "code"
        self.results_dir = self.project_root / "data" / "results"
        self.report_path = self.results_dir / "lint_report.txt"

        # Ensure directories exist
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def test_lint_report_exists(self):
        """Test that the lint report is generated after running the script."""
        # Run the linting script
        script_path = self.project_root / "code" / "039_run_linting.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )

        # Check that the report file exists
        self.assertTrue(
            self.report_path.exists(),
            f"Lint report not found at {self.report_path}"
        )

    def test_lint_report_content(self):
        """Test that the lint report contains expected sections."""
        # Run the linting script first
        script_path = self.project_root / "code" / "039_run_linting.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )

        # Read the report
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for expected sections
        self.assertIn("RUFF CHECK:", content)
        self.assertIn("BLACK FORMAT:", content)
        self.assertIn("SUMMARY:", content)
        self.assertIn("Exit Code:", content)

    def test_code_directory_processed(self):
        """Test that the code directory was actually processed."""
        # Run the linting script
        script_path = self.project_root / "code" / "039_run_linting.py"
        subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )

        # Read the report
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify the code directory path is mentioned
        self.assertIn("code", content.lower())

if __name__ == "__main__":
    unittest.main()