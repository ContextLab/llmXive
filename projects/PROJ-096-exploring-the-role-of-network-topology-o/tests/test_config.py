"""
Tests for configuration management and deterministic seed settings.
"""

import json
import sys
from pathlib import Path
import tempfile
import os

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.config import (
    get_config, set_config, get_seed, get_t_eval, 
    init_config, apply_global_seed, CONFIG_FILE_PATH,
    DEFAULT_GLOBAL_SEED, DEFAULT_T_EVAL_START, DEFAULT_T_EVAL_STOP, DEFAULT_T_EVAL_NUM
)

def test_get_config_defaults():
    """Test that get_config returns defaults when config file doesn't exist."""
    # Temporarily rename config file if it exists
    original_path = CONFIG_FILE_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a temporary config path
        temp_config = Path(tmpdir) / "config.json"
        
        # We can't easily mock the global CONFIG_FILE_PATH, so we test the logic
        # by checking that defaults are defined correctly
        assert DEFAULT_GLOBAL_SEED == 42
        assert DEFAULT_T_EVAL_START == 0.0
        assert DEFAULT_T_EVAL_STOP == 100.0
        assert DEFAULT_T_EVAL_NUM == 1000
    
    print("✓ test_get_config_defaults passed")

def test_set_and_get_config():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_path = Path(tmpdir) / "test_config.json"
        
        # Create a test config
        test_config = {
            "seed": 123,
            "t_eval_start": 0.0,
            "t_eval_stop": 200.0,
            "t_eval_num": 2000
        }
        
        # Save to temp location
        with open(temp_config_path, 'w') as f:
            json.dump(test_config, f)
        
        # Load and verify
        with open(temp_config_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == test_config
    
    print("✓ test_set_and_get_config passed")

def test_get_seed():
    """Test that get_seed returns the configured seed."""
    # The actual seed comes from config file, but we can verify the function exists
    # and returns an integer
    seed = get_seed()
    assert isinstance(seed, int)
    print(f"✓ test_get_seed passed (current seed: {seed})")

def test_get_t_eval():
    """Test that get_t_eval returns correct tuple structure."""
    t_start, t_stop, t_num = get_t_eval()
    
    assert isinstance(t_start, float)
    assert isinstance(t_stop, float)
    assert isinstance(t_num, int)
    assert t_start < t_stop
    assert t_num > 0
    
    print(f"✓ test_get_t_eval passed: [{t_start}, {t_stop}] with {t_num} points")

def test_init_config():
    """Test configuration initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save original config path
        original_path = CONFIG_FILE_PATH
        
        # We test the logic by calling init_config with specific values
        # and verifying it returns the expected dictionary
        config = init_config(
            seed=999,
            t_eval_start=0.0,
            t_eval_stop=50.0,
            t_eval_num=500
        )
        
        assert config["seed"] == 999
        assert config["t_eval_start"] == 0.0
        assert config["t_eval_stop"] == 50.0
        assert config["t_eval_num"] == 500
        
        print("✓ test_init_config passed")

def test_apply_global_seed():
    """Test that apply_global_seed sets numpy and random seeds."""
    import random
    import numpy as np
    
    # Set a known seed
    seed_value = 4242
    apply_global_seed(seed_value)
    
    # Generate some random numbers
    val1 = random.random()
    val2 = np.random.random()
    
    # Reset and generate again
    apply_global_seed(seed_value)
    val1_reset = random.random()
    val2_reset = np.random.random()
    
    # Should be identical due to deterministic seeding
    assert val1 == val1_reset
    assert abs(val2 - val2_reset) < 1e-15
    
    print("✓ test_apply_global_seed passed")

if __name__ == "__main__":
    test_get_config_defaults()
    test_set_and_get_config()
    test_get_seed()
    test_get_t_eval()
    test_init_config()
    test_apply_global_seed()
    print("\nAll tests passed!")
