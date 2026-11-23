"""
Integration tests for linting and formatting tools.
Verifies that ruff and black can be executed against the codebase.
"""
import os
import sys
import unittest
import subprocess
from pathlib import Path

class TestLintingIntegration(unittest.TestCase):
    """Integration tests for linting tools."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.code_dir = self.project_root / "code"

    @unittest.skipIf(
        not subprocess.run(["which", "ruff"], capture_output=True).returncode == 0,
        "ruff not installed"
    )
    def test_ruff_check_runs(self):
        """Test that ruff check can be executed."""
        result = subprocess.run(
            ["ruff", "check", str(self.code_dir)],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        # We expect this to run without crashing, even if there are linting errors
        self.assertIn(result.returncode, [0, 1], "ruff check crashed unexpectedly")

    @unittest.skipIf(
        not subprocess.run(["which", "black"], capture_output=True).returncode == 0,
        "black not installed"
    )
    def test_black_check_runs(self):
        """Test that black check can be executed."""
        result = subprocess.run(
            ["black", "--check", str(self.code_dir)],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        # We expect this to run without crashing, even if files need formatting
        self.assertIn(result.returncode, [0, 1], "black check crashed unexpectedly")

    def test_setup_linting_script_runs(self):
        """Test that the setup_linting.py script runs successfully."""
        script_path = self.code_dir / "setup_linting.py"
        self.assertTrue(script_path.exists(), "setup_linting.py does not exist")

        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        self.assertEqual(result.returncode, 0, f"setup_linting.py failed: {result.stderr}")

if __name__ == "__main__":
    unittest.main()