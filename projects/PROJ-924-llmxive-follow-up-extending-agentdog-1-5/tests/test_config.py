"""
Tests for the configuration module (config.py).
"""
import pytest
import os
import random
import numpy as np
from pathlib import Path

from code.config import (
    set_seed,
    get_config,
    get_config_summary,
    get_path,
    get_output_path,
    ensure_directories,
    get_batch_size,
    get_max_memory_gb,
    get_drift_threshold,
    get_centroid_model,
    get_baseline_model,
    RANDOM_SEED,
    MAX_RAM_GB,
    BATCH_SIZE,
)


def test_constants_exist():
    """Test that required constants are defined."""
    assert RANDOM_SEED == 42, f"Expected RANDOM_SEED=42, got {RANDOM_SEED}"
    assert MAX_RAM_GB == 7, f"Expected MAX_RAM_GB=7, got {MAX_RAM_GB}"
    assert BATCH_SIZE == 64, f"Expected BATCH_SIZE=64, got {BATCH_SIZE}"


def test_get_batch_size():
    """Test that get_batch_size returns the correct value."""
    assert get_batch_size() == 64


def test_get_max_memory_gb():
    """Test that get_max_memory_gb returns the correct value."""
    assert get_max_memory_gb() == 7


def test_get_drift_threshold():
    """Test that get_drift_threshold returns a float."""
    threshold = get_drift_threshold()
    assert isinstance(threshold, float)


def test_get_centroid_model():
    """Test that get_centroid_model returns the correct model name."""
    assert get_centroid_model() == "all-MiniLM-L6-v2"


def test_get_baseline_model():
    """Test that get_baseline_model returns the correct model name."""
    assert get_baseline_model() == "google/flan-t5-small"


def test_set_seed_determinism():
    """Test that set_seed produces deterministic results."""
    # Set seed
    set_seed(42)
    val1 = random.random()
    arr1 = np.random.random(5)

    # Reset seed
    set_seed(42)
    val2 = random.random()
    arr2 = np.random.random(5)

    # Verify determinism
    assert val1 == val2
    np.testing.assert_array_equal(arr1, arr2)


def test_set_seed_updates_config():
    """Test that set_seed updates the internal configuration."""
    set_seed(123)
    config = get_config()
    assert config["random_seed"] == 123


def test_get_config_summary():
    """Test that get_config_summary returns expected keys."""
    summary = get_config_summary()
    assert "random_seed" in summary
    assert "max_ram_gb" in summary
    assert "batch_size" in summary
    assert "centroid_model" in summary
    assert "baseline_model" in summary
    assert "drift_threshold" in summary


def test_get_path_valid():
    """Test that get_path returns a valid Path for known keys."""
    path = get_path("data_raw")
    assert isinstance(path, Path)
    assert path.name == "raw"


def test_get_path_invalid():
    """Test that get_path raises KeyError for unknown keys."""
    with pytest.raises(KeyError, match="not found in configuration"):
        get_path("non_existent_path")


def test_get_output_path():
    """Test that get_output_path constructs the correct path."""
    output_path = get_output_path("data_processed", "test.csv")
    assert output_path.name == "test.csv"
    assert output_path.parent.name == "processed"


def test_ensure_directories_creates_dirs(tmp_path):
    """Test that ensure_directories creates the required directories."""
    # Temporarily override project root
    from code import config
    original_root = config._config["project_root"]
    config._config["project_root"] = tmp_path

    try:
        # Ensure specific paths
        ensure_directories(["data_raw", "data_processed"])
        
        # Verify directories exist
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()
    finally:
        # Restore original root
        config._config["project_root"] = original_root
