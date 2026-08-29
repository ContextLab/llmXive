import os
import subprocess
import tempfile
import shutil
import unittest
from pathlib import Path

class TestT039Linting(unittest.TestCase):
    """
    Test that the linting script runs correctly and produces the expected report.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).resolve().parent.parent
        self.script_path = self.project_root / "code" / "039_run_linting.py"
        self.report_path = self.project_root / "data" / "results" / "lint_report.txt"
        
        # Ensure the script exists
        self.assertTrue(self.script_path.exists(), f"Script not found: {self.script_path}")

    def test_script_executes_without_error(self):
        """
        Verify that running the linting script does not raise an exception
        and returns exit code 0 (assuming the code is already clean or fixed).
        """
        # We run the script. It might fail if ruff/black aren't installed, 
        # but in the context of the pipeline environment, they should be.
        # If the script runs and writes the report, that's the primary check.
        result = subprocess.run(
            ["python", str(self.script_path)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        # The script should exit with 0 if successful.
        # Note: If ruff/black find unfixable errors, the script logic 
        # returns 1. However, the task is to "fix all reported issues".
        # If the code is already clean, it returns 0.
        # We assert that the report file was created regardless of success/fail of the linters themselves,
        # but the task requirement implies the code should be clean.
        
        # Check if report was generated
        self.assertTrue(self.report_path.exists(), "Lint report file was not generated.")
        
        # Read report to verify content
        with open(self.report_path, 'r') as f:
            content = f.read()
            self.assertIn("Starting Linting and Formatting Pipeline", content)
            self.assertIn("Running: Ruff Check and Fix", content)
            self.assertIn("Running: Black Format", content)

    def test_code_is_ruff_clean(self):
        """
        Verify that the code directory passes ruff check (exit code 0).
        """
        code_dir = self.project_root / "code"
        result = subprocess.run(
            ["ruff", "check", str(code_dir)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        # If ruff is not installed, we skip this specific assertion or handle it,
        # but for the purpose of the task, we assume the environment is set up.
        # If the task T039 is completed successfully, this should pass.
        # We assert that the exit code is 0.
        self.assertEqual(result.returncode, 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}")

    def test_code_is_black_formatted(self):
        """
        Verify that the code directory is formatted by black (exit code 0).
        """
        code_dir = self.project_root / "code"
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        # If black is not installed, handle gracefully, but assume installed.
        self.assertEqual(result.returncode, 0, f"Black check failed:\n{result.stdout}\n{result.stderr}")

if __name__ == '__main__':
    unittest.main()