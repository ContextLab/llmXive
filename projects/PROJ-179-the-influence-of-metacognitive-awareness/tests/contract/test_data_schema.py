"""
Contract test for the data validation script (T006).

The test checks that the validation report is created and that it contains a
``status`` field with either ``PASS`` or ``FAIL``.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import unittest

class TestDataSchema(unittest.TestCase):
    """Ensures the validation report follows the declared JSON schema."""

    def setUp(self):
        # Ensure a clean state before each test
        repo_root = Path(__file__).resolve().parents[3]
        self.report_path = repo_root / "data" / "validation_report.json"
        if self.report_path.is_file():
            self.report_path.unlink()

    def test_validation_report_created(self):
        """Run the validator and verify the JSON file exists."""
        # Execute the validator script
        repo_root = Path(__file__).resolve().parents[3]
        script_path = repo_root / "code" / "data" / "validate_data.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # The script should exit with 0 or 1 (both are acceptable for the contract)
        self.assertIn(result.returncode, (0, 1), msg="Validator did not exit cleanly")

        # The report file must exist after execution
        self.assertTrue(
            self.report_path.is_file(),
            msg="validation_report.json was not created by the validator",
        )

    def test_validation_report_schema(self):
        """The JSON must contain a top‑level ``status`` key with a valid value."""
        # Run the validator (it will generate the report)
        repo_root = Path(__file__).resolve().parents[3]
        script_path = repo_root / "code" / "data" / "validate_data.py"
        subprocess.run([sys.executable, str(script_path)], cwd=repo_root)

        with open(self.report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertIn(
            "status",
            report,
            msg="validation_report.json missing required 'status' key",
        )
        self.assertIn(
            report["status"],
            ("PASS", "FAIL"),
            msg="validation_report.json 'status' must be 'PASS' or 'FAIL'",
        )

if __name__ == "__main__":
    unittest.main()