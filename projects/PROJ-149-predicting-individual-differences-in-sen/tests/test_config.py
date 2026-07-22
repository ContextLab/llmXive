import os
import sys
import pytest
from pathlib import Path
import numpy as np
import random

# Add project root to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import (
    set_global_seed, 
    ensure_dirs, 
    get_path, 
    get_band_freqs, 
    get_all_band_names, 
    get_filter_params,
    load_config,
    ROOT_DIR,
    DATA_DIR
)

def test_set_global_seed():
    """Test that set_global_seed sets seeds for random and numpy."""
    set_global_seed(12345)
    assert random.randint(0, 100) == random.randint(0, 100) # Reset and check determinism
    
    # Reset seed again
    set_global_seed(12345)
    val1 = random.randint(0, 100)
    
    set_global_seed(12345)
    val2 = random.randint(0, 100)
    
    assert val1 == val2, "Random seed not set correctly"

def test_ensure_dirs():
    """Test that ensure_dirs creates required directories."""
    # Temporarily test on a subdirectory to avoid cluttering if needed, 
    # but ensure_dirs is designed to run once at startup.
    # Here we just verify it doesn't crash and directories exist.
    ensure_dirs()
    assert DATA_DIR.exists()
    assert (DATA_DIR / "processed").exists()

def test_get_path_valid():
    """Test get_path returns correct paths for valid keys."""
    assert get_path("data_processed") == DATA_DIR / "processed"
    assert get_path("figures") == ROOT_DIR / "figures"

def test_get_path_invalid():
    """Test get_path raises KeyError for invalid keys."""
    with pytest.raises(KeyError):
        get_path("non_existent_key")

def test_get_band_freqs():
    """Test band frequency definitions."""
    bands = get_band_freqs()
    assert "delta" in bands
    assert bands["delta"] == (1.0, 4.0)
    assert "gamma" in bands
    assert bands["gamma"] == (30.0, 40.0)

def test_get_all_band_names():
    """Test retrieval of band names."""
    names = get_all_band_names()
    expected = ["delta", "theta", "alpha", "low_beta", "high_beta", "gamma"]
    assert names == expected

def test_get_filter_params():
    """Test filter parameter retrieval."""
    params = get_filter_params()
    assert params["bandpass_low"] == 1.0
    assert params["bandpass_high"] == 40.0
    assert 50.0 in params["notch_freqs"]

def test_load_config():
    """Test loading configuration (should load defaults if file missing)."""
    config = load_config()
    assert "seed" in config
    assert "paths" in config
    assert config["seed"] == 42 # Default seed
