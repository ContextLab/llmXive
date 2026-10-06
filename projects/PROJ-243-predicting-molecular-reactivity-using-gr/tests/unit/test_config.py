import os
import tempfile
import pytest
from unittest.mock import patch

def test_default_config_structure():
    """Test that get_default_config returns the expected keys."""
    from config import get_default_config
    
    cfg = get_default_config()
    
    assert 'project_root' in cfg
    assert 'data_root' in cfg
    assert 'code_root' in cfg
    assert 'artifacts_root' in cfg
    assert 'tests_root' in cfg
    assert 'seed' in cfg
    assert 'directories' in cfg
    assert 'log_level' in cfg

def test_ensure_directories_creates_folders():
    """Test that ensure_directories creates the specified folders."""
    from config import get_default_config, ensure_directories
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = get_default_config()
        cfg['project_root'] = tmpdir
        
        # Ensure directories exist
        ensure_directories(cfg)
        
        # Check a few key directories
        assert os.path.isdir(os.path.join(tmpdir, 'data', 'raw'))
        assert os.path.isdir(os.path.join(tmpdir, 'data', 'processed'))
        assert os.path.isdir(os.path.join(tmpdir, 'artifacts'))
        assert os.path.isdir(os.path.join(tmpdir, 'tests', 'unit'))

def test_set_seed():
    """Test that set_seed sets the random seeds."""
    import random
    import numpy as np
    from config import set_seed
    
    set_seed(123)
    val1 = random.random()
    val2 = np.random.random()
    
    set_seed(123)
    val3 = random.random()
    val4 = np.random.random()
    
    assert val1 == val3
    assert val2 == val4