import unittest
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import PathConfig, get_config, ensure_directories


class TestConfigPaths(unittest.TestCase):
    """Tests specifically for path definitions and directory creation."""

    def setUp(self):
        import config
        config._global_config = None

    def tearDown(self):
        import config
        config._global_config = None

    def test_path_config_relative_to_project_root(self):
        """Verify paths are relative to the project root (code/../)."""
        # The default implementation in config.py uses os.path.dirname twice to go up from code/config.py
        # to the project root.
        cfg = get_config().paths
        # Check that base_dir is the parent of the directory containing config.py
        expected_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertEqual(cfg.base_dir, expected_base)

    def test_trajectory_path_formation(self):
        """Verify trajectory path is formed correctly."""
        cfg = get_config().paths
        expected = os.path.join(cfg.results_dir, "trajectory.json")
        self.assertEqual(cfg.trajectory_path, expected)

    def test_trade_off_path_formation(self):
        """Verify trade off path is formed correctly."""
        cfg = get_config().paths
        expected = os.path.join(cfg.results_dir, "trade_off_analysis.json")
        self.assertEqual(cfg.trade_off_path, expected)

    def test_state_path_formation(self):
        """Verify state path is formed correctly."""
        cfg = get_config().paths
        expected = os.path.join(cfg.results_dir, "state.json")
        self.assertEqual(cfg.state_path, expected)