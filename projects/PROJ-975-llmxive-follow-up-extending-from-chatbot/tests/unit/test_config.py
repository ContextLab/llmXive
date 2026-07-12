"""
Unit tests for config module - T037 reproducibility verification.
"""
import os
import sys
import pytest
import numpy as np
import random

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import get_seeds, get_experiment_config, pin_seeds, validate_reproducibility, SEED_A, SEED_B

def test_seeds_loaded_from_environment():
    """Test that seeds are loaded from environment variables."""
    seeds = get_seeds()
    assert 'SEED_A' in seeds
    assert 'SEED_B' in seeds
    assert isinstance(seeds['SEED_A'], int)
    assert isinstance(seeds['SEED_B'], int)

def test_default_seeds():
    """Test default seed values when environment variables not set."""
    # Temporarily clear environment
    old_seed_a = os.environ.get('SEED_A')
    old_seed_b = os.environ.get('SEED_B')
    
    if 'SEED_A' in os.environ:
        del os.environ['SEED_A']
    if 'SEED_B' in os.environ:
        del os.environ['SEED_B']
    
    # Reload module to get defaults
    import importlib
    import config
    importlib.reload(config)
    
    assert config.SEED_A == 42
    assert config.SEED_B == 123
    
    # Restore
    if old_seed_a:
        os.environ['SEED_A'] = old_seed_a
    if old_seed_b:
        os.environ['SEED_B'] = old_seed_b

def test_experiment_config_structure():
    """Test that experiment config contains all required fields."""
    config = get_experiment_config()
    assert 'seeds' in config
    assert 'library_sizes' in config
    assert 'overlap_levels' in config
    assert 'pinned_seeds' in config
    assert 'force_cpu' in config
    
    assert config['library_sizes'] == [10, 30, 50, 100]
    assert 'low' in config['overlap_levels']
    assert 'medium' in config['overlap_levels']
    assert 'high' in config['overlap_levels']

def test_pin_seeds_reproducibility():
    """Test that pin_seeds ensures reproducibility."""
    pin_seeds()
    
    # Generate random values
    val1 = random.random()
    np_val1 = np.random.random()
    
    # Reset and generate again
    pin_seeds()
    val2 = random.random()
    np_val2 = np.random.random()
    
    assert val1 == val2
    assert np_val1 == np_val2

def test_validate_reproducibility():
    """Test reproducibility validation."""
    result = validate_reproducibility()
    assert result is True
