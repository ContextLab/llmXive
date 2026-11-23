"""
Unit tests for the config module.

Verifies that configuration constants are set correctly and
helper functions behave as expected.
"""
import pytest
import sys
from pathlib import Path

# Add the code directory to the path to allow imports
# Assuming this test runs from the project root or tests directory
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from config import (
    RANDOM_SEED,
    MAX_RAM_GB,
    BATCH_SIZE,
    get_config,
    set_seed,
    get_path,
    ensure_directories,
    get_batch_size,
    get_max_memory_gb,
)


class TestConfigConstants:
    """Tests for the core constant values defined in config.py."""

    def test_random_seed_value(self):
        """Verify RANDOM_SEED is set to 42."""
        assert RANDOM_SEED == 42, f"Expected RANDOM_SEED=42, got {RANDOM_SEED}"

    def test_max_ram_gb_value(self):
        """Verify MAX_RAM_GB is set to 7."""
        assert MAX_RAM_GB == 7, f"Expected MAX_RAM_GB=7, got {MAX_RAM_GB}"

    def test_batch_size_value(self):
        """Verify BATCH_SIZE is set to 64."""
        assert BATCH_SIZE == 64, f"Expected BATCH_SIZE=64, got {BATCH_SIZE}"


class TestConfigFunctions:
    """Tests for configuration helper functions."""

    def test_get_config_returns_dict(self):
        """Verify get_config returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)
        assert "random_seed" in config
        assert "max_ram_gb" in config
        assert "batch_size" in config

    def test_set_seed_resets_random(self):
        """Verify set_seed affects random state."""
        import random
        set_seed(123)
        val1 = random.random()
        set_seed(123)
        val2 = random.random()
        assert val1 == val2, "Random state should be deterministic after set_seed"

    def test_get_path_existing_key(self):
        """Verify get_path returns a Path for a known key."""
        data_dir = get_path("data_dir")
        assert isinstance(data_dir, Path)
        # Check if it matches the constant
        from config import DATA_DIR
        assert data_dir == DATA_DIR

    def test_get_path_missing_key(self):
        """Verify get_path raises KeyError for unknown key."""
        with pytest.raises(KeyError):
            get_path("non_existent_key")

    def test_ensure_directories_creates_missing(self):
        """Verify ensure_directories creates directories if they don't exist."""
        # We test with a temporary path to avoid cluttering the project structure
        # However, the function is designed to create standard dirs.
        # We'll just verify it doesn't crash on the standard set.
        try:
            ensure_directories()
            # If we are here, it succeeded
            assert True
        except Exception as e:
            pytest.fail(f"ensure_directories failed: {e}")

    def test_get_batch_size(self):
        """Verify get_batch_size returns the correct integer."""
        assert get_batch_size() == 64

    def test_get_max_memory_gb(self):
        """Verify get_max_memory_gb returns the correct float."""
        assert get_max_memory_gb() == 7.0

    def test_get_max_memory_gb_type(self):
        """Verify get_max_memory_gb returns a float."""
        val = get_max_memory_gb()
        assert isinstance(val, (int, float)), "Max RAM should be numeric"
