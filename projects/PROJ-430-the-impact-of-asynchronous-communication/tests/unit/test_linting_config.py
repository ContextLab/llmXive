"""
Unit tests for linting and formatting configuration.
Verifies that configuration files are created correctly and contain expected settings.
"""
import os
import tempfile
import unittest
from pathlib import Path

# Import the setup script logic for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_linting import RUFF_CONFIG, BLACK_CONFIG


class TestLintingConfig(unittest.TestCase):
    """Tests for linting and formatting configuration generation."""

    def test_ruff_config_contains_required_sections(self):
        """Verify Ruff config contains essential sections."""
        self.assertIn("[lint]", RUFF_CONFIG)
        self.assertIn("select =", RUFF_CONFIG)
        self.assertIn("line-length =", RUFF_CONFIG)
        self.assertIn("[lint.isort]", RUFF_CONFIG)

    def test_black_config_contains_required_settings(self):
        """Verify Black config contains essential settings."""
        self.assertIn("[tool.black]", BLACK_CONFIG)
        self.assertIn("line-length =", BLACK_CONFIG)
        self.assertIn("target-version =", BLACK_CONFIG)
        self.assertIn("exclude =", BLACK_CONFIG)

    def test_line_length_consistency(self):
        """Ensure both tools use the same line length (100)."""
        import re
        
        ruff_match = re.search(r'line-length = (\d+)', RUFF_CONFIG)
        black_match = re.search(r'line-length = (\d+)', BLACK_CONFIG)
        
        self.assertIsNotNone(ruff_match, "Ruff config missing line-length")
        self.assertIsNotNone(black_match, "Black config missing line-length")
        
        ruff_length = int(ruff_match.group(1))
        black_length = int(black_match.group(1))
        
        self.assertEqual(ruff_length, 100, "Ruff line-length should be 100")
        self.assertEqual(black_length, 100, "Black line-length should be 100")
        self.assertEqual(ruff_length, black_length, "Line lengths must match between tools")

    def test_python_version_target(self):
        """Verify target Python version is 3.11."""
        self.assertIn("py311", BLACK_CONFIG)

    def test_exclude_directories(self):
        """Verify common directories are excluded from formatting."""
        excluded_dirs = [".git", "data", "figures", "build", "dist"]
        
        for directory in excluded_dirs:
            self.assertIn(directory, RUFF_CONFIG, f"Ruff should exclude {directory}")
            self.assertIn(directory, BLACK_CONFIG, f"Black should exclude {directory}")


if __name__ == "__main__":
    unittest.main()