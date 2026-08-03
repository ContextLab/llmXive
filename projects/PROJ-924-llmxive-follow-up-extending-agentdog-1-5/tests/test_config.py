import pytest
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

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
    get_drift_threshold,
    get_centroid_model,
    get_baseline_model,
)

def test_random_seed_constant():
    """Verify RANDOM_SEED is set to 42."""
    assert RANDOM_SEED == 42

def test_max_ram_gb_constant():
    """Verify MAX_RAM_GB is set to 7."""
    assert MAX_RAM_GB == 7

def test_batch_size_constant():
    """Verify BATCH_SIZE is set to 64."""
    assert BATCH_SIZE == 64

def test_get_config_returns_dict():
    """Verify get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict)
    assert "random_seed" in config
    assert "max_ram_gb" in config
    assert "batch_size" in config

def test_set_seed():
    """Verify set_seed sets the random seed."""
    import random
    import numpy as np
    
    # Reset seed to a known value
    set_seed(123)
    
    # Generate a random number
    val1 = random.random()
    
    # Reset seed to the same value
    set_seed(123)
    
    # Generate a random number again
    val2 = random.random()
    
    assert val1 == val2

def test_get_path_root():
    """Verify get_path returns correct paths."""
    root = get_path("root")
    assert root.exists()
    
    code = get_path("code")
    assert code.exists()
    assert code.name == "code"

def test_ensure_directories():
    """Verify ensure_directories creates necessary folders."""
    # Just check it doesn't raise an exception
    ensure_directories()
    
    # Verify specific directories exist
    assert get_path("data_raw").exists()
    assert get_path("data_processed").exists()
    assert get_path("data_test").exists()

def test_get_batch_size():
    """Verify get_batch_size returns the configured value."""
    assert get_batch_size() == 64

def test_get_max_memory_gb():
    """Verify get_max_memory_gb returns the configured value."""
    assert get_max_memory_gb() == 7

def test_get_drift_threshold():
    """Verify get_drift_threshold returns a float."""
    threshold = get_drift_threshold()
    assert isinstance(threshold, float)
    assert 0.0 < threshold < 1.0

def test_get_centroid_model():
    """Verify get_centroid_model returns a string."""
    model = get_centroid_model()
    assert isinstance(model, str)
    assert len(model) > 0

def test_get_baseline_model():
    """Verify get_baseline_model returns a string."""
    model = get_baseline_model()
    assert isinstance(model, str)
    assert len(model) > 0