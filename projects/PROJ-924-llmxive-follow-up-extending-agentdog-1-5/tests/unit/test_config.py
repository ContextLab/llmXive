"""
Unit tests for config.py
"""
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

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
        assert RANDOM_SEED == 42

    def test_max_ram_gb_is_7(self):
        assert MAX_RAM_GB == 7

    def test_batch_size_is_64(self):
        assert BATCH_SIZE == 64


class TestConfigFunctions:
    """Test configuration management functions."""

    def test_set_seed(self):
        set_seed(123)
        import random
        import numpy as np
        assert random.randint(0, 100) == random.randint(0, 100) # This is a weak check, but set_seed is called
        # Better check:
        set_seed(42)
        val1 = random.random()
        set_seed(42)
        val2 = random.random()
        assert val1 == val2

    def test_get_config_returns_dict(self):
        config = get_config()
        assert isinstance(config, dict)
        assert "random_seed" in config

    def test_update_config(self):
        original = get_config()["batch_size"]
        update_config("batch_size", 128)
        assert get_config()["batch_size"] == 128
        # Reset
        update_config("batch_size", original)

    def test_get_config_summary(self):
        summary = get_config_summary()
        assert isinstance(summary, str)
        assert "Seed:" in summary

    def test_get_path_existing(self):
        path = get_path("project_root")
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_path_missing_key(self):
        with pytest.raises(KeyError):
            get_path("non_existent_key")

    def test_get_output_path(self):
        path = get_output_path("test.csv")
        assert "processed" in str(path)
        assert path.name == "test.csv"

    def test_ensure_directories_creates_missing(self):
        # This might create dirs if they don't exist
        dirs = ensure_directories()
        for d in dirs:
            assert d.exists()

    def test_get_batch_size(self):
        assert get_batch_size() == 64

    def test_get_max_memory_gb(self):
        assert get_max_memory_gb() == 7

    def test_get_drift_threshold(self):
        assert get_drift_threshold() == 1.5

    def test_get_centroid_model(self):
        assert get_centroid_model() == "all-MiniLM-L6-v2"

    def test_get_baseline_model(self):
        assert get_baseline_model() == "facebook/bart-large-mnli"
