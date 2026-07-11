"""
Unit tests for configuration management.
"""
import pytest
from pathlib import Path
import tempfile
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import (
    load_config, 
    get_project_paths, 
    ensure_directories,
    get_seed,
    get_tolerance,
    get_matrix_size,
    get_num_eigenvalues,
    get_perturbation_norm,
    get_sparsity_density,
    get_num_mc_iterations,
    DEFAULTS
)

def test_get_project_paths_structure():
    """Test that project paths have the expected structure."""
    paths = get_project_paths()
    
    assert "root" in paths
    assert "code" in paths
    assert "data" in paths
    assert "figures" in paths
    assert "specs" in paths
    assert "state" in paths
    
    # Check data subdirectories
    assert "raw" in paths["data"]
    assert "processed" in paths["data"]
    assert "logs" in paths["data"]
    assert "figures" in paths["data"]
    
    # Check that paths are Path objects
    assert isinstance(paths["root"], Path)
    assert isinstance(paths["code"], Path)

def test_load_config_with_default():
    """Test loading config with default path (non-existent file)."""
    config = load_config("non_existent_file.yaml")
    
    # Should return defaults
    assert config["random_seed"] == DEFAULTS["random_seed"]
    assert config["tolerance"] == DEFAULTS["tolerance"]

def test_load_config_with_custom_file():
    """Test loading config from a custom YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        custom_config = {
            "random_seed": 123,
            "tolerance": 1e-8,
            "matrix_size": 2000,
            "custom_param": "test_value"
        }
        yaml.dump(custom_config, f)
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        
        assert config["random_seed"] == 123
        assert config["tolerance"] == 1e-8
        assert config["matrix_size"] == 2000
        assert config["custom_param"] == "test_value"
        
        # Defaults should still be present for non-specified keys
        assert config["num_eigenvalues"] == DEFAULTS["num_eigenvalues"]
    finally:
        Path(temp_path).unlink()

def test_get_seed():
    """Test seed retrieval functions."""
    config = {"random_seed": 999}
    assert get_seed(config) == 999
    
    assert get_seed(None) == DEFAULTS["random_seed"]

def test_get_tolerance():
    """Test tolerance retrieval functions."""
    config = {"tolerance": 1e-5}
    assert get_tolerance(config) == 1e-5
    
    assert get_tolerance(None) == DEFAULTS["tolerance"]

def test_get_matrix_size():
    """Test matrix size retrieval functions."""
    config = {"matrix_size": 500}
    assert get_matrix_size(config) == 500
    
    assert get_matrix_size(None) == DEFAULTS["matrix_size"]

def test_get_num_eigenvalues():
    """Test eigenvalue count retrieval functions."""
    config = {"num_eigenvalues": 20}
    assert get_num_eigenvalues(config) == 20
    
    assert get_num_eigenvalues(None) == DEFAULTS["num_eigenvalues"]

def test_get_perturbation_norm():
    """Test perturbation norm retrieval functions."""
    config = {"perturbation_norm": 3.5}
    assert get_perturbation_norm(config) == 3.5
    
    assert get_perturbation_norm(None) == DEFAULTS["perturbation_norm"]

def test_get_sparsity_density():
    """Test sparsity density retrieval functions."""
    config = {"sparsity_density": 0.5}
    assert get_sparsity_density(config) == 0.5
    
    assert get_sparsity_density(None) == DEFAULTS["sparsity_density"]

def test_get_num_mc_iterations():
    """Test Monte Carlo iteration count retrieval functions."""
    config = {"num_mc_iterations": 500}
    assert get_num_mc_iterations(config) == 500
    
    assert get_num_mc_iterations(None) == DEFAULTS["num_mc_iterations"]

def test_ensure_directories():
    """Test that ensure_directories creates the expected structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock paths by temporarily changing the working directory
        import os
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            # Create a mock project structure
            code_dir = Path(tmpdir) / "code"
            code_dir.mkdir()
            utils_dir = code_dir / "utils"
            utils_dir.mkdir()
            
            # Create a temporary config file
            config_file = Path(tmpdir) / "config.yaml"
            config_file.write_text("random_seed: 42\n")
            
            # Call ensure_directories
            ensure_directories()
            
            # Verify directories were created
            data_raw = Path(tmpdir) / "data" / "raw"
            data_processed = Path(tmpdir) / "data" / "processed"
            data_logs = Path(tmpdir) / "data" / "logs"
            data_figures = Path(tmpdir) / "data" / "figures"
            figures = Path(tmpdir) / "figures"
            state = Path(tmpdir) / "state"
            
            assert data_raw.exists()
            assert data_processed.exists()
            assert data_logs.exists()
            assert data_figures.exists()
            assert figures.exists()
            assert state.exists()
        finally:
            os.chdir(old_cwd)