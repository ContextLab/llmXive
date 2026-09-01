"""
Unit tests for configuration management and seed pinning (Task T006).

These tests verify:
1. ProjectConfig initializes paths correctly relative to project root.
2. set_seed() correctly pins seeds for random, numpy, and optionally torch.
3. Path helpers return absolute paths.
4. Deterministic behavior is achieved when seeds are pinned.
"""
import os
import random
from pathlib import Path
import tempfile
import pytest

import numpy as np

# Import the module under test
from code.utils.config import (
    ProjectConfig, 
    get_config, 
    set_seed, 
    get_data_path, 
    get_output_path, 
    get_code_path
)

def test_project_config_initialization():
    """Test that ProjectConfig initializes paths correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock project structure
        project_root = Path(tmpdir)
        config = ProjectConfig(project_root=project_root)
        
        assert config.project_root == project_root.resolve()
        assert config.data_dir == project_root / "data"
        assert config.code_dir == project_root / "code"
        assert config.output_dir == project_root / "data/processed"
        assert config.logs_dir == project_root / "data/logs"
        
        # Verify directories were created
        assert config.data_dir.exists()
        assert config.output_dir.exists()
        assert config.logs_dir.exists()

def test_project_config_path_helpers():
    """Test that path helpers return correct absolute paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        config = ProjectConfig(project_root=project_root)
        
        data_path = config.get_data_path("raw/studies.csv")
        assert data_path == project_root / "data/raw/studies.csv"
        
        output_path = config.get_output_path("results.json")
        assert output_path == project_root / "data/processed/results.json"
        
        code_path = config.get_code_path("analysis/model.py")
        assert code_path == project_root / "code/analysis/model.py"

def test_set_seed_defaults():
    """Test that set_seed uses default seed from config when None is passed."""
    # Reset global config to ensure clean state
    import code.utils.config as config_module
    config_module._config = None
    
    config = get_config()
    default_seed = config.random_seed
    
    set_seed()  # Should use default
    
    # Verify random state is deterministic
    val1 = random.random()
    set_seed()  # Reset to same seed
    val2 = random.random()
    
    assert val1 == val2

def test_set_seed_custom_value():
    """Test that set_seed works with custom seed values."""
    seed = 12345
    set_seed(seed)
    
    val1 = random.random()
    np_val1 = np.random.random()
    
    set_seed(seed)
    val2 = random.random()
    np_val2 = np.random.random()
    
    assert val1 == val2
    assert np_val1 == np_val2

def test_set_seed_negative_raises():
    """Test that set_seed raises ValueError for negative seeds."""
    with pytest.raises(ValueError, match="Seed must be a non-negative integer"):
        set_seed(-1)

def test_deterministic_numpy():
    """Test that numpy operations are deterministic after set_seed."""
    seed = 42
    set_seed(seed)
    
    arr1 = np.random.rand(10, 10)
    
    set_seed(seed)
    arr2 = np.random.rand(10, 10)
    
    assert np.array_equal(arr1, arr2)

def test_environment_variable_set():
    """Test that PYTHONHASHSEED is set correctly."""
    seed = 999
    set_seed(seed)
    
    assert os.environ.get('PYTHONHASHSEED') == str(seed)

def test_get_config_singleton():
    """Test that get_config returns the same instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

def test_path_helpers_use_singleton():
    """Test that path helpers use the global config singleton."""
    # Reset to ensure clean state
    import code.utils.config as config_module
    config_module._config = None
    
    # Initialize config
    config = get_config()
    
    # Verify helpers return paths based on this config
    data_path = get_data_path("test.csv")
    assert data_path == config.get_data_path("test.csv")
    
    output_path = get_output_path("test.json")
    assert output_path == config.get_output_path("test.json")
    
    code_path = get_code_path("test.py")
    assert code_path == config.get_code_path("test.py")