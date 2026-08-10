"""
Tests for the config module.
"""
import pytest
from pathlib import Path
import sys
import os

# Add the code directory to the path so we can import config
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import (
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
    RANDOM_SEED,
    MAX_RAM_GB,
    BATCH_SIZE
)

def test_random_seed_constant():
    """Verify the RANDOM_SEED constant is 42."""
    assert RANDOM_SEED == 42

def test_max_ram_constant():
    """Verify the MAX_RAM_GB constant is 7."""
    assert MAX_RAM_GB == 7

def test_batch_size_constant():
    """Verify the BATCH_SIZE constant is 64."""
    assert BATCH_SIZE == 64

def test_set_seed():
    """Test that set_seed updates the internal seed."""
    set_seed(123)
    assert get_config()["random_seed"] == 123
    # Reset to default for other tests
    set_seed(RANDOM_SEED)

def test_get_config():
    """Test that get_config returns a dictionary with expected keys."""
    cfg = get_config()
    assert isinstance(cfg, dict)
    assert "random_seed" in cfg
    assert "max_ram_gb" in cfg
    assert "batch_size" in cfg
    assert "paths" in cfg

def test_update_config():
    """Test updating a config value."""
    update_config("drift_threshold", 0.8)
    assert get_config()["drift_threshold"] == 0.8
    # Reset
    update_config("drift_threshold", 0.5)

def test_get_path():
    """Test retrieving paths from config."""
    raw_path = get_path("raw")
    assert isinstance(raw_path, Path)
    assert raw_path.name == "raw"

    # Test invalid key
    with pytest.raises(KeyError):
        get_path("invalid_path_name")

def test_get_output_path():
    """Test constructing output paths."""
    out_path = get_output_path("drift_results", "scores.csv")
    assert isinstance(out_path, Path)
    assert out_path.name == "scores.csv"
    assert "processed" in str(out_path)
    assert "drift_results" in str(out_path)

def test_ensure_directories():
    """Test that ensure_directories creates the necessary folders."""
    # Get a path that might not exist yet
    test_dir = get_path("processed") / "test_ensure_directories"
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    # We can't easily test creation of all paths without side effects,
    # but we can ensure it doesn't crash.
    ensure_directories()
    # Verify at least the root processed dir exists
    assert get_path("processed").exists()

def test_getters():
    """Test specific getter functions."""
    assert get_batch_size() == 64
    assert get_max_memory_gb() == 7
    assert get_drift_threshold() == 0.5
    assert get_centroid_model() == "all-MiniLM-L6-v2"
    assert get_baseline_model() == "google/flan-t5-small"

def test_config_summary():
    """Test that get_config_summary returns a string."""
    summary = get_config_summary()
    assert isinstance(summary, str)
    assert "Seed" in summary