"""
Unit tests for the config module.
"""
import pytest
import os
import sys
from pathlib import Path

# Add the code directory to the path for imports
# Assuming the test is run from the project root or similar context
# We need to dynamically locate the 'code' directory relative to this test file
test_dir = Path(__file__).resolve().parent
project_root = test_dir.parent.parent  # projects/PROJ-.../tests -> projects/PROJ-...
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
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
    """Verify that the RANDOM_SEED constant is 42."""
    assert RANDOM_SEED == 42

def test_max_ram_constant():
    """Verify that the MAX_RAM_GB constant is 7."""
    assert MAX_RAM_GB == 7

def test_batch_size_constant():
    """Verify that the BATCH_SIZE constant is 64."""
    assert BATCH_SIZE == 64

def test_set_seed_updates_config():
    """Verify that set_seed updates the internal configuration."""
    original_seed = get_config()["random_seed"]
    test_seed = 12345
    set_seed(test_seed)
    assert get_config()["random_seed"] == test_seed
    # Restore original
    set_seed(original_seed)

def test_get_batch_size():
    """Verify get_batch_size returns the correct value."""
    assert get_batch_size() == 64

def test_get_max_memory_gb():
    """Verify get_max_memory_gb returns the correct value."""
    assert get_max_memory_gb() == 7

def test_get_drift_threshold():
    """Verify get_drift_threshold returns the correct default."""
    assert get_drift_threshold() == 0.5

def test_get_centroid_model():
    """Verify get_centroid_model returns the correct model."""
    assert get_centroid_model() == "all-MiniLM-L6-v2"

def test_get_baseline_model():
    """Verify get_baseline_model returns the correct model."""
    assert get_baseline_model() == "google/flan-t5-small"

def test_get_path_valid_key():
    """Verify get_path returns a Path for a valid key."""
    path = get_path("project_root")
    assert isinstance(path, Path)
    assert path.exists()

def test_get_path_invalid_key():
    """Verify get_path raises KeyError for an invalid key."""
    with pytest.raises(KeyError):
        get_path("non_existent_key")

def test_update_config():
    """Verify update_config modifies the configuration."""
    original_batch = get_config()["batch_size"]
    update_config({"batch_size": 128})
    assert get_config()["batch_size"] == 128
    # Restore
    update_config({"batch_size": original_batch})

def test_get_config_summary():
    """Verify get_config_summary returns a string."""
    summary = get_config_summary()
    assert isinstance(summary, str)
    assert "Seed" in summary
    assert "Max RAM" in summary
    assert "Batch Size" in summary

def test_ensure_directories():
    """Verify ensure_directories creates the required directories."""
    # Get a temporary test dir to ensure we don't clutter
    # But since the function creates specific dirs, we just check it runs without error
    try:
        ensure_directories()
        # Check that the main project dir exists
        assert get_path("project_dir").exists()
    except Exception as e:
        pytest.fail(f"ensure_directories raised an exception: {e}")

def test_get_output_path():
    """Verify get_output_path constructs the correct path."""
    path = get_output_path("test_file.csv")
    assert "processed" in str(path)
    assert path.name == "test_file.csv"