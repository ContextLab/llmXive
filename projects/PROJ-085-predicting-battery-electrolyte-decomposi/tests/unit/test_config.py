import pytest
import os
from pathlib import Path

from config import (
    get_project_root, get_seed, set_seed, 
    get_dataset_url, set_dataset_url,
    get_processed_dir, get_raw_dir,
    get_config, is_debug_mode, set_debug_mode
)

class TestConfig:
    """Tests for environment configuration management (T009)."""

    def test_get_project_root(self):
        """Test that project root is a valid Path."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_seed_management(self):
        """Test setting and getting the seed."""
        original = get_seed()
        set_seed(12345)
        assert get_seed() == 12345
        set_seed(original) # Reset

    def test_dataset_url_management(self):
        """Test setting and getting dataset URL."""
        original = get_dataset_url()
        set_dataset_url("http://test.com/data")
        assert get_dataset_url() == "http://test.com/data"
        set_dataset_url(original) # Reset

    def test_directory_paths(self):
        """Test that directory paths are constructed correctly."""
        root = get_project_root()
        assert get_processed_dir().is_absolute()
        assert get_raw_dir().is_absolute()
        # Check they are under project root
        assert str(get_processed_dir()).startswith(str(root))

    def test_debug_mode(self):
        """Test debug mode toggling."""
        original = is_debug_mode()
        set_debug_mode(True)
        assert is_debug_mode() is True
        set_debug_mode(original)

    def test_config_dict(self):
        """Test getting the full config dict."""
        cfg = get_config()
        assert "seed" in cfg
        assert "dataset_url" in cfg
        assert isinstance(cfg, dict)
