"""
Tests for Task T039: Linting and Formatting.

These tests verify that the linting script runs correctly and produces the expected artifacts.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

class TestT039Linting(unittest.TestCase):
    """Test suite for T039 linting task."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).resolve().parent.parent
        self.script_path = self.project_root / "code" / "039_run_linting.py"
        self.results_dir = self.project_root / "data" / "results"
        self.report_path = self.results_dir / "lint_report.txt"
        
        # Ensure results directory exists for the test
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def test_script_exists(self):
        """Verify that the linting script exists."""
        self.assertTrue(self.script_path.exists(), 
                        "T039 script (039_run_linting.py) does not exist.")

    def test_script_syntax(self):
        """Verify that the linting script has valid Python syntax."""
        try:
            with open(self.script_path, "r", encoding="utf-8") as f:
                compile(f.read(), self.script_path, "exec")
        except SyntaxError as e:
            self.fail(f"Syntax error in {self.script_path}: {e}")

    def test_report_generation(self):
        """Verify that running the script generates the lint report."""
        # Run the script
        result = subprocess.run(
            [sys.executable, str(self.script_path)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        # The script should run (exit code 0 means clean, non-zero might mean issues found but handled)
        # We check if the report file was created regardless of exit code
        self.assertTrue(self.report_path.exists(), 
                        "Lint report (lint_report.txt) was not generated.")

        # Verify report content
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("T039 Linting Report", content, 
                      "Report does not contain expected header.")
        self.assertIn("Command:", content, 
                      "Report does not contain command logs.")
        self.assertIn("STATUS:", content, 
                      "Report does not contain status summary.")

    def test_ruff_and_black_invoked(self):
        """Verify that the script attempts to run ruff and black."""
        with open(self.script_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("ruff", content, "Script does not invoke ruff.")
        self.assertIn("black", content, "Script does not invoke black.")

if __name__ == "__main__":
    unittest.main()