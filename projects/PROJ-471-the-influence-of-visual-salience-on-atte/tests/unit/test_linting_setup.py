"""
Unit tests for linting setup configuration.
Verifies that ruff and black configurations are present and valid.
"""
import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestLintingSetup(unittest.TestCase):
    """Tests for linting configuration files."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.code_dir = self.project_root / "code"

    def test_ruff_config_exists(self):
        """Test that ruff configuration file exists."""
        ruff_config = self.code_dir / ".ruff.toml"
        self.assertTrue(ruff_config.exists(), "Ruff configuration file does not exist")

    def test_black_config_exists(self):
        """Test that black configuration file exists."""
        black_config = self.code_dir / ".black.toml"
        self.assertTrue(black_config.exists(), "Black configuration file does not exist")

    def test_ruff_config_valid_toml(self):
        """Test that ruff configuration is valid TOML."""
        ruff_config = self.code_dir / ".ruff.toml"
        try:
            import tomllib
            with open(ruff_config, "rb") as f:
                tomllib.load(f)
        except ImportError:
            try:
                import toml
                with open(ruff_config, "r") as f:
                    toml.load(f)
            except Exception as e:
                self.fail(f"Ruff configuration is not valid TOML: {e}")

    def test_black_config_valid_toml(self):
        """Test that black configuration is valid TOML."""
        black_config = self.code_dir / ".black.toml"
        try:
            import tomllib
            with open(black_config, "rb") as f:
                tomllib.load(f)
        except ImportError:
            try:
                import toml
                with open(black_config, "r") as f:
                    toml.load(f)
            except Exception as e:
                self.fail(f"Black configuration is not valid TOML: {e}")

    def test_requirements_includes_linting_tools(self):
        """Test that requirements.txt includes ruff and black."""
        req_file = self.project_root / "requirements.txt"
        self.assertTrue(req_file.exists(), "requirements.txt does not exist")

        with open(req_file, "r") as f:
            content = f.read().lower()

        self.assertIn("ruff", content, "ruff not found in requirements.txt")
        self.assertIn("black", content, "black not found in requirements.txt")

if __name__ == "__main__":
    unittest.main()
