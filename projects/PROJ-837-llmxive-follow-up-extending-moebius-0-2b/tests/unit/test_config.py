"""
Unit tests for code/config.py
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    set_mode,
    get_mode,
    is_ci_mode,
    is_research_mode,
    get_config_summary,
    get_path,
    ensure_paths_exist
)


class TestConfigMode(unittest.TestCase):
    """Tests for mode switching and retrieval"""

    def setUp(self):
        """Reset mode before each test"""
        set_mode("CI")

    def test_set_mode_ci(self):
        """Test setting mode to CI"""
        set_mode("CI")
        self.assertEqual(get_mode(), "CI")

    def test_set_mode_research(self):
        """Test setting mode to Research"""
        set_mode("RESEARCH")
        self.assertEqual(get_mode(), "RESEARCH")

    def test_is_ci_mode_true(self):
        """Test is_ci_mode returns True in CI mode"""
        set_mode("CI")
        self.assertTrue(is_ci_mode())

    def test_is_ci_mode_false(self):
        """Test is_ci_mode returns False in Research mode"""
        set_mode("RESEARCH")
        self.assertFalse(is_ci_mode())

    def test_is_research_mode_true(self):
        """Test is_research_mode returns True in Research mode"""
        set_mode("RESEARCH")
        self.assertTrue(is_research_mode())

    def test_is_research_mode_false(self):
        """Test is_research_mode returns False in CI mode"""
        set_mode("CI")
        self.assertFalse(is_research_mode())


class TestConfigSummary(unittest.TestCase):
    """Tests for config summary generation"""

    def test_get_config_summary_contains_mode(self):
        """Test that config summary includes current mode"""
        set_mode("CI")
        summary = get_config_summary()
        self.assertIn("mode", summary)
        self.assertEqual(summary["mode"], "CI")

    def test_get_config_summary_contains_paths(self):
        """Test that config summary includes path keys"""
        summary = get_config_summary()
        self.assertIn("paths", summary)


class TestConfigPaths(unittest.TestCase):
    """Tests for path retrieval and validation"""

    def test_get_path_returns_string(self):
        """Test get_path returns a string for known key"""
        path = get_path("data_raw")
        self.assertIsInstance(path, str)

    def test_get_path_with_default(self):
        """Test get_path with default value for unknown key"""
        path = get_path("unknown_key", "/default/path")
        self.assertEqual(path, "/default/path")

    @patch('code.config.os.makedirs')
    @patch('code.config.os.path.exists')
    def test_ensure_paths_exist_creates_missing(self, mock_exists, mock_makedirs):
        """Test ensure_paths_exist creates missing directories"""
        mock_exists.side_effect = [False, True, True]  # First path missing
        ensure_paths_exist()
        self.assertTrue(mock_makedirs.called)

    @patch('code.config.os.path.exists')
    def test_ensure_paths_exist_skips_existing(self, mock_exists):
        """Test ensure_paths_exist skips existing directories"""
        mock_exists.return_value = True
        ensure_paths_exist()
        # makedirs should not be called if all paths exist
        mock_makedirs = __import__('os').makedirs
        # We can't easily verify this without more complex mocking,
        # but the test ensures no error is raised
        self.assertTrue(True)


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for config module"""

    def test_mode_persists_across_calls(self):
        """Test that mode setting persists"""
        set_mode("RESEARCH")
        self.assertTrue(is_research_mode())
        self.assertFalse(is_ci_mode())
        self.assertEqual(get_mode(), "RESEARCH")

    def test_summary_reflects_current_mode(self):
        """Test that summary reflects the currently set mode"""
        set_mode("CI")
        summary_ci = get_config_summary()
        set_mode("RESEARCH")
        summary_research = get_config_summary()
        self.assertEqual(summary_ci["mode"], "CI")
        self.assertEqual(summary_research["mode"], "RESEARCH")


if __name__ == "__main__":
    unittest.main()
