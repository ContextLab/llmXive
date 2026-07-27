"""
Tests for linting and formatting configuration.
Verifies that ruff and black are installed and can run against the codebase.
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest

class TestLintingConfig(unittest.TestCase):
    """Test cases for linting configuration."""

    def test_ruff_is_installed(self):
        """Test that ruff is installed and returns a version."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("ruff", result.stdout.lower())
        except FileNotFoundError:
            self.fail("ruff is not installed or not in PATH")
        except subprocess.TimeoutExpired:
            self.fail("ruff command timed out")

    def test_black_is_installed(self):
        """Test that black is installed and returns a version."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("black", result.stdout.lower())
        except FileNotFoundError:
            self.fail("black is not installed or not in PATH")
        except subprocess.TimeoutExpired:
            self.fail("black command timed out")

    def test_ruff_can_check_code(self):
        """Test that ruff can run a check on the code directory without crashing."""
        code_dir = Path(__file__).parent.parent
        if not code_dir.exists():
            self.skipTest("code directory does not exist")

        try:
            result = subprocess.run(
                ["ruff", "check", str(code_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Return code 0 means no errors, 1 means errors found (which is fine for this test)
            # We just want to ensure it runs without crashing (e.g., syntax error in config)
            # Return code 2 would indicate a configuration or usage error.
            self.assertNotEqual(result.returncode, 2, msg=f"Ruff config error: {result.stderr}")
        except FileNotFoundError:
            self.fail("ruff not found")
        except subprocess.TimeoutExpired:
            self.fail("ruff check timed out")

    def test_black_can_format_code(self):
        """Test that black can run a check (dry-run) on the code directory."""
        code_dir = Path(__file__).parent.parent
        if not code_dir.exists():
            self.skipTest("code directory does not exist")

        try:
            result = subprocess.run(
                ["black", "--check", "--diff", str(code_dir)],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Return code 0 means formatted correctly, 1 means needs formatting
            # We just want to ensure it runs without crashing (return code 2)
            self.assertNotEqual(result.returncode, 2, msg=f"Black config error: {result.stderr}")
        except FileNotFoundError:
            self.fail("black not found")
        except subprocess.TimeoutExpired:
            self.fail("black check timed out")

if __name__ == "__main__":
    unittest.main()
