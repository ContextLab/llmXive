"""
Unit tests for the environment_manager module.
Verifies config loading, seed setting, and path creation.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import yaml
import random
import numpy as np

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.environment_manager import (
    load_config, 
    setup_reproducibility, 
    get_paths, 
    get_config_value,
    deep_merge,
    _config
)

def test_deep_merge():
    """Test the deep_merge utility function."""
    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 20, "e": 5}, "f": 6}
    result = deep_merge(base, override)
    
    assert result["a"] == 1
    assert result["b"]["c"] == 20
    assert result["b"]["d"] == 3
    assert result["b"]["e"] == 5
    assert result["f"] == 6
    print("✓ test_deep_merge passed")

def test_load_config_defaults():
    """Test that config loads defaults when file is missing."""
    # Reset global cache to force reload
    import utils.environment_manager as em
    em._config = None
    
    # Temporarily rename config if it exists in the real project
    config_path = PROJECT_ROOT / "code" / "config.yaml"
    backup_path = PROJECT_ROOT / "code" / "config.yaml.bak"
    moved = False
    
    if config_path.exists():
        config_path.rename(backup_path)
        moved = True
    
    try:
        cfg = load_config()
        assert cfg["random_seed"] == 42
        assert cfg["ivt_velocity_threshold"] == 30
        assert cfg["data"]["raw_dir"] == "data/raw"
        print("✓ test_load_config_defaults passed")
    finally:
        # Restore original config
        em._config = None
        if moved:
            backup_path.rename(config_path)

def test_setup_reproducibility():
    """Test that seeds are set correctly."""
    # Reset seed to a known non-42 value first
    random.seed(12345)
    np.random.seed(12345)
    
    # Call setup with explicit seed
    setup_reproducibility(seed=999)
    
    assert random.getstate()[1][0] != 12345  # State should have changed
    # Note: We can't easily check numpy's internal state without regenerating,
    # but we trust the function calls np.random.seed(999).
    # Let's verify by generating a number.
    val1 = random.random()
    setup_reproducibility(seed=999)
    val2 = random.random()
    assert val1 == val2, "Random seed should be reproducible"
    print("✓ test_setup_reproducibility passed")

def test_get_paths_creates_dirs():
    """Test that get_paths creates directories."""
    # Use a temporary directory for the test to avoid clutter
    # We mock the PROJECT_ROOT in the module
    import utils.environment_manager as em
    original_root = em.PROJECT_ROOT
    
    with tempfile.TemporaryDirectory() as tmpdir:
        em.PROJECT_ROOT = Path(tmpdir)
        em._config = None # Force reload
        
        # Create a fake config to point to tmpdir subfolders
        fake_config = {
            "data": {
                "raw_dir": "test_raw",
                "derived_dir": "test_derived"
            },
            "random_seed": 42
        }
        em._config = fake_config
        
        paths = get_paths()
        
        assert "raw" in paths
        assert paths["raw"].exists()
        assert paths["raw"].name == "test_raw"
        assert "derived" in paths
        assert paths["derived"].exists()
        
        print("✓ test_get_paths_creates_dirs passed")
    
    # Restore
    em.PROJECT_ROOT = original_root
    em._config = None

def test_get_config_value():
    """Test retrieving specific config values."""
    import utils.environment_manager as em
    em._config = None
    em._config = {"a": {"b": {"c": 123}}, "d": 456}
    
    assert get_config_value("a.b.c") == 123
    assert get_config_value("d") == 456
    assert get_config_value("a.b.x", default="missing") == "missing"
    assert get_config_value("nonexistent") is None
    
    print("✓ test_get_config_value passed")

if __name__ == "__main__":
    test_deep_merge()
    test_load_config_defaults()
    test_setup_reproducibility()
    test_get_paths_creates_dirs()
    test_get_config_value()
    print("\nAll environment manager tests passed.")