import os
import random
import numpy as np
import pytest
from pathlib import Path
from utils.config import set_global_seed, get_config, ensure_directories

def test_set_global_seed_determinism():
    """Test that setting the seed produces deterministic results."""
    set_global_seed(42)
    val1 = random.random()
    arr1 = np.random.rand(3)
    
    set_global_seed(42)
    val2 = random.random()
    arr2 = np.random.rand(3)
    
    assert val1 == val2
    np.testing.assert_array_equal(arr1, arr2)

def test_get_config_returns_dict():
    """Test that get_config returns a dictionary."""
    config = get_config()
    assert isinstance(config, dict)
    assert 'seed' in config

def test_ensure_directories_creates_folders(tmp_path):
    """Test that ensure_directories creates the required folder structure."""
    # Mock the config to use a temp directory
    import utils.config
    original_get_config = utils.config.get_config
    
    def mock_get_config():
        return {'data_dirs': {'raw': str(tmp_path / 'raw'), 
                              'processed': str(tmp_path / 'processed'),
                              'tests': str(tmp_path / 'tests')}}
    
    utils.config.get_config = mock_get_config
    
    try:
        ensure_directories()
        
        assert (tmp_path / 'raw').exists()
        assert (tmp_path / 'processed').exists()
        assert (tmp_path / 'tests').exists()
    finally:
        utils.config.get_config = original_get_config