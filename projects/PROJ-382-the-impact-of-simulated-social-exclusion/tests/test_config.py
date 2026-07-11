"""
Tests for the configuration loader (code/config.py).
"""
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from config import (
    load_config,
    get_osf_urls,
    get_project_root,
    get_data_dirs,
    get_config_value,
)


class TestConfigLoader(TestCase):
    """Test suite for config.py functions."""

    def setUp(self):
        """Create a temporary directory and config file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.yaml")
        
        # Create a valid test config
        self.test_config = {
            "project": {
                "name": "PROJ-382-test",
                "version": "1.0.0"
            },
            "data_sources": {
                "osf_urls": [
                    "https://osf.io/abc123",
                    "https://osf.io/def456"
                ],
                "local_path": "/data/local"
            },
            "settings": {
                "random_seed": 42,
                "max_retries": 3
            }
        }
        
        with open(self.config_path, "w") as f:
            yaml.dump(self.test_config, f)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)

    def test_load_config_valid_file(self):
        """Test loading a valid YAML config file."""
        config = load_config(self.config_path)
        self.assertEqual(config["project"]["name"], "PROJ-382-test")
        self.assertIn("osf_urls", config["data_sources"])

    def test_load_config_missing_file(self):
        """Test that FileNotFoundError is raised for missing config."""
        with self.assertRaises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_get_osf_urls(self):
        """Test extraction of OSF URLs from config."""
        config = load_config(self.config_path)
        urls = get_osf_urls(config)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://osf.io/abc123")

    def test_get_osf_urls_missing_key(self):
        """Test ValueError when data_sources key is missing."""
        bad_config = {"other_key": "value"}
        with self.assertRaises(ValueError):
            get_osf_urls(bad_config)

    def test_get_osf_urls_not_list(self):
        """Test ValueError when osf_urls is not a list."""
        bad_config = {"data_sources": {"osf_urls": "not_a_list"}}
        with self.assertRaises(ValueError):
            get_osf_urls(bad_config)

    def test_get_config_value_dot_notation(self):
        """Test retrieving nested values with dot notation."""
        config = load_config(self.config_path)
        self.assertEqual(get_config_value("project.name", config=config), "PROJ-382-test")
        self.assertEqual(get_config_value("data_sources.osf_urls.0", config=config), "https://osf.io/abc123")
        self.assertIsNone(get_config_value("nonexistent.key", config=config))
        self.assertEqual(get_config_value("nonexistent.key", default="fallback", config=config), "fallback")

    def test_get_data_dirs_structure(self):
        """Test that data directory paths are correctly constructed."""
        # Mock get_project_root to return temp_dir for predictable paths
        with patch("config.get_project_root", return_value=Path(self.temp_dir)):
            dirs = get_data_dirs()
            self.assertIn("raw", dirs)
            self.assertIn("processed", dirs)
            self.assertIn("figures", dirs)
            self.assertEqual(str(dirs["raw"]), os.path.join(self.temp_dir, "data", "raw"))