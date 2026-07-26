"""
Test suite to verify linting and formatting configuration.
This test ensures that the project's ruff and black configurations
are present and can be invoked successfully.
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import unittest

class TestLintingConfig(unittest.TestCase):
    """Tests for linting and formatting tool configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        self.ruff_config = self.project_root / ".ruff.toml"
        self.pyproject_config = self.project_root / "pyproject.toml"
        
        # Verify config files exist
        self.assertTrue(self.ruff_config.exists(), ".ruff.toml must exist")
        self.assertTrue(self.pyproject_config.exists(), "pyproject.toml must exist")

    def test_ruff_config_syntax_valid(self):
        """Verify that .ruff.toml is a valid TOML file."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(self.ruff_config, "rb") as f:
            config = tomllib.load(f)
        
        self.assertIn("lint", config)
        self.assertIn("format", config)

    def test_black_config_in_pyproject(self):
        """Verify that black configuration exists in pyproject.toml."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(self.pyproject_config, "rb") as f:
            config = tomllib.load(f)
        
        self.assertIn("tool", config)
        self.assertIn("black", config["tool"])
        self.assertEqual(config["tool"]["black"]["line-length"], 88)

    def test_ruff_can_check_code(self):
        """Verify that ruff can run a check on the codebase."""
        # Run ruff check on a small subset to verify configuration works
        result = subprocess.run(
            ["ruff", "check", "code/utils/config.py"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        # We expect success (exit code 0) or lint warnings (exit code 1)
        # We do NOT expect a configuration error (exit code 2)
        self.assertNotEqual(result.returncode, 2, f"Ruff configuration error: {result.stderr}")

    def test_black_can_format_code(self):
        """Verify that black can run a check on the codebase."""
        result = subprocess.run(
            ["black", "--check", "--diff", "code/utils/config.py"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        # Black returns 0 if clean, 1 if changes needed, 2 if error
        self.assertNotEqual(result.returncode, 2, f"Black configuration error: {result.stderr}")

    def test_ruff_config_contains_expected_rules(self):
        """Verify that the ruff config includes the expected linting rules."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(self.ruff_config, "rb") as f:
            config = tomllib.load(f)
        
        select_rules = config["lint"]["select"]
        self.assertIn("E", select_rules)
        self.assertIn("F", select_rules)
        self.assertIn("W", select_rules)
        self.assertIn("I", select_rules)

    def test_black_config_contains_expected_settings(self):
        """Verify that the black config includes expected settings."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(self.pyproject_config, "rb") as f:
            config = tomllib.load(f)
        
        black_config = config["tool"]["black"]
        self.assertEqual(black_config["line-length"], 88)
        self.assertIn("py311", black_config["target-version"])

if __name__ == "__main__":
    unittest.main()