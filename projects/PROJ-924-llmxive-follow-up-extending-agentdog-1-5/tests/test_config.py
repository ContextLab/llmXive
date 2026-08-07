"""
Tests for the config module.
"""
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
# This assumes tests are run from the project root or similar structure
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import (
    RANDOM_SEED,
    MAX_RAM_GB,
    BATCH_SIZE,
    get_config,
    set_seed,
    get_path,
    get_batch_size,
    get_max_memory_gb,
    ensure_directories,
    get_config_summary
)

class TestConfigConstants:
    """Tests for the core constants in config.py"""

    def test_random_seed_is_42(self):
        """Verify RANDOM_SEED is set to 42"""
        assert RANDOM_SEED == 42

    def test_max_ram_gb_is_7(self):
        """Verify MAX_RAM_GB is set to 7"""
        assert MAX_RAM_GB == 7

    def test_batch_size_is_64(self):
        """Verify BATCH_SIZE is set to 64"""
        assert BATCH_SIZE == 64

class TestConfigFunctions:
    """Tests for config utility functions"""

    def test_get_config_returns_dict(self):
        """Verify get_config returns a dictionary"""
        config = get_config()
        assert isinstance(config, dict)
        assert "random_seed" in config
        assert "max_ram_gb" in config
        assert "batch_size" in config

    def test_get_batch_size_returns_integer(self):
        """Verify get_batch_size returns an integer"""
        batch_size = get_batch_size()
        assert isinstance(batch_size, int)
        assert batch_size == 64

    def test_get_max_memory_gb_returns_integer(self):
        """Verify get_max_memory_gb returns an integer"""
        max_ram = get_max_memory_gb()
        assert isinstance(max_ram, int)
        assert max_ram == 7

    def test_set_seed_updates_global_state(self):
        """Verify set_seed updates the internal configuration"""
        original_seed = get_config()["random_seed"]
        set_seed(12345)
        new_config = get_config()
        assert new_config["random_seed"] == 12345
        # Reset to original
        set_seed(original_seed)

    def test_get_path_resolves_relative_path(self):
        """Verify get_path constructs an absolute path"""
        test_path = get_path("data/raw")
        assert isinstance(test_path, Path)
        assert test_path.is_absolute()
        assert test_path.name == "raw"

    def test_ensure_directories_creates_folders(self, tmp_path):
        """Verify ensure_directories creates directories"""
        # Temporarily override project root for testing
        import config
        original_root = config._config["project_root"]
        
        try:
            # Use a temp directory as project root
            config._config["project_root"] = tmp_path
            
            # Ensure a nested path exists
            test_dir = "test_output/subdir"
            ensure_directories([test_dir])
            
            assert (tmp_path / test_dir).exists()
            assert (tmp_path / test_dir).is_dir()
        finally:
            # Restore original root
            config._config["project_root"] = original_root

    def test_get_config_summary_produces_string(self):
        """Verify get_config_summary returns a non-empty string"""
        summary = get_config_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Random Seed" in summary
        assert "Max RAM" in summary
        assert "Batch Size" in summary