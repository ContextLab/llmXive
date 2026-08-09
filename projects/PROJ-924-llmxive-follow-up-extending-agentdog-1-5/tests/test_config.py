"""
Tests for the config module.

Verifies that configuration constants are set correctly and 
helper functions behave as expected.
"""
import pytest
import random
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import (
    RANDOM_SEED,
    MAX_RAM_GB,
    BATCH_SIZE,
    set_seed,
    get_config,
    update_config,
    get_config_summary,
    get_path,
    get_output_path,
    ensure_directories,
    get_batch_size,
    get_max_memory_gb,
    get_drift_threshold,
    get_centroid_model,
    get_baseline_model,
)


class TestConfigConstants:
    """Test that core constants are defined correctly."""

    def test_random_seed_is_42(self):
        """Verify RANDOM_SEED is 42."""
        assert RANDOM_SEED == 42

    def test_max_ram_gb_is_7(self):
        """Verify MAX_RAM_GB is 7."""
        assert MAX_RAM_GB == 7

    def test_batch_size_is_64(self):
        """Verify BATCH_SIZE is 64."""
        assert BATCH_SIZE == 64


class TestSetSeed:
    """Test the set_seed function."""

    def test_set_seed_affects_random(self):
        """Verify set_seed affects python random module."""
        set_seed(123)
        val1 = random.random()
        set_seed(123)
        val2 = random.random()
        assert val1 == val2

    def test_set_seed_affects_numpy(self):
        """Verify set_seed affects numpy."""
        set_seed(456)
        arr1 = np.random.rand(5)
        set_seed(456)
        arr2 = np.random.rand(5)
        assert np.array_equal(arr1, arr2)

    def test_set_seed_default(self):
        """Verify set_seed uses RANDOM_SEED when called without args."""
        set_seed()
        val1 = random.random()
        set_seed()
        val2 = random.random()
        assert val1 == val2


class TestGetConfig:
    """Test configuration retrieval."""

    def test_get_config_returns_dict(self):
        """Verify get_config returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)

    def test_get_config_contains_seed(self):
        """Verify config contains random_seed."""
        config = get_config()
        assert "random_seed" in config

    def test_get_config_contains_max_ram(self):
        """Verify config contains max_ram_gb."""
        config = get_config()
        assert "max_ram_gb" in config

    def test_get_config_contains_batch_size(self):
        """Verify config contains batch_size."""
        config = get_config()
        assert "batch_size" in config


class TestUpdateConfig:
    """Test configuration updates."""

    def test_update_config_changes_value(self):
        """Verify update_config modifies the config."""
        original_seed = get_config()["random_seed"]
        update_config("random_seed", 999)
        assert get_config()["random_seed"] == 999
        # Reset
        update_config("random_seed", original_seed)


class TestGetPath:
    """Test path resolution functions."""

    def test_get_path_returns_project_root(self):
        """Verify get_path() returns project root."""
        path = get_path()
        assert path.exists()

    def test_get_path_with_relative(self):
        """Verify get_path resolves relative paths."""
        path = get_path("data/raw")
        assert "data" in str(path)
        assert "raw" in str(path)


class TestGetOutputPath:
    """Test output path generation."""

    def test_get_output_path_raw(self):
        """Verify get_output_path for raw data."""
        path = get_output_path("raw", "test.json")
        assert "raw" in str(path)
        assert path.name == "test.json"

    def test_get_output_path_processed(self):
        """Verify get_output_path for processed data."""
        path = get_output_path("processed", "test.csv")
        assert "processed" in str(path)

    def test_get_output_path_invalid_type(self):
        """Verify get_output_path raises ValueError for unknown type."""
        with pytest.raises(ValueError):
            get_output_path("invalid_type", "test.txt")


class TestEnsureDirectories:
    """Test directory creation."""

    def test_ensure_directories_creates_folders(self):
        """Verify ensure_directories creates required folders."""
        # This might already exist, but it should not raise
        ensure_directories()
        
        config = get_config()
        assert config["data_raw_dir"].exists()
        assert config["data_processed_dir"].exists()
        assert config["data_test_dir"].exists()


class TestGetters:
    """Test specific getter functions."""

    def test_get_batch_size(self):
        """Verify get_batch_size returns correct value."""
        assert get_batch_size() == 64

    def test_get_max_memory_gb(self):
        """Verify get_max_memory_gb returns correct value."""
        assert get_max_memory_gb() == 7

    def test_get_drift_threshold(self):
        """Verify get_drift_threshold returns a float."""
        val = get_drift_threshold()
        assert isinstance(val, float)
        assert val > 0.0

    def test_get_centroid_model(self):
        """Verify get_centroid_model returns a string."""
        model = get_centroid_model()
        assert isinstance(model, str)
        assert len(model) > 0

    def test_get_baseline_model(self):
        """Verify get_baseline_model returns a string."""
        model = get_baseline_model()
        assert isinstance(model, str)
        assert len(model) > 0

    def test_get_config_summary(self):
        """Verify get_config_summary returns a string."""
        summary = get_config_summary()
        assert isinstance(summary, str)
        assert "Random Seed" in summary