"""
Unit tests for the configuration loader module.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config_loader import (
    load_yaml_config,
    load_simulation_config,
    load_missingness_config,
    load_estimation_config,
    get_missingness_rate,
    load_all_configs,
    CONFIG_DIR
)


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory with config files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config_path = tmp_path / "config"
        config_path.mkdir()

        # Create simulation.yaml
        sim_config = {
            'sample_size': 500,
            'true_effect': 0.75,
            'seed': 123,
            'beta0': 0.0,
            'beta1': 1.0,
            'beta2': 0.3,
            'sigma': 0.5
        }
        with open(config_path / "simulation.yaml", 'w') as f:
            yaml.dump(sim_config, f)

        # Create missingness.yaml
        miss_config = {
            'mechanisms': ['mcar', 'mar'],
            'rates': {
                'mcar': 0.1,
                'mar': 0.2
            }
        }
        with open(config_path / "missingness.yaml", 'w') as f:
            yaml.dump(miss_config, f)

        # Create estimation.yaml
        est_config = {
            'bandwidth_rule': 'IK',
            'imputation_count': 3,
            'nominal_confidence': 0.90
        }
        with open(config_path / "estimation.yaml", 'w') as f:
            yaml.dump(est_config, f)

        yield config_path


def test_load_yaml_config_valid(temp_config_dir):
    """Test loading a valid YAML file."""
    config_file = temp_config_dir / "simulation.yaml"
    config = load_yaml_config(config_file)
    
    assert isinstance(config, dict)
    assert config['sample_size'] == 500
    assert config['true_effect'] == 0.75


def test_load_yaml_config_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_yaml_config(Path("/nonexistent/path/config.yaml"))


def test_load_yaml_config_empty(tmp_path):
    """Test loading an empty YAML file."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")
    
    config = load_yaml_config(empty_file)
    assert config == {}


def test_load_simulation_config_valid(temp_config_dir):
    """Test loading valid simulation configuration."""
    # Mock the CONFIG_DIR path
    import src.config_loader as config_loader_module
    original_dir = config_loader_module.CONFIG_DIR
    config_loader_module.CONFIG_DIR = temp_config_dir

    try:
        config = load_simulation_config()
        assert config['sample_size'] == 500
        assert config['true_effect'] == 0.75
        assert config['seed'] == 123
    finally:
        config_loader_module.CONFIG_DIR = original_dir


def test_load_simulation_config_missing_keys(temp_config_dir):
    """Test that ValueError is raised for missing required keys."""
    # Create a file with missing keys
    with open(temp_config_dir / "simulation.yaml", 'w') as f:
        yaml.dump({'sample_size': 100}, f)

    import src.config_loader as config_loader_module
    original_dir = config_loader_module.CONFIG_DIR
    config_loader_module.CONFIG_DIR = temp_config_dir

    try:
        with pytest.raises(ValueError, match="Missing required keys"):
            load_simulation_config()
    finally:
        config_loader_module.CONFIG_DIR = original_dir


def test_load_missingness_config_valid(temp_config_dir):
    """Test loading valid missingness configuration."""
    import src.config_loader as config_loader_module
    original_dir = config_loader_module.CONFIG_DIR
    config_loader_module.CONFIG_DIR = temp_config_dir

    try:
        config = load_missingness_config()
        assert 'mcar' in config['mechanisms']
        assert config['rates']['mcar'] == 0.1
    finally:
        config_loader_module.CONFIG_DIR = original_dir


def test_load_estimation_config_valid(temp_config_dir):
    """Test loading valid estimation configuration."""
    import src.config_loader as config_loader_module
    original_dir = config_loader_module.CONFIG_DIR
    config_loader_module.CONFIG_DIR = temp_config_dir

    try:
        config = load_estimation_config()
        assert config['bandwidth_rule'] == 'IK'
        assert config['imputation_count'] == 3
        assert config['nominal_confidence'] == 0.90
    finally:
        config_loader_module.CONFIG_DIR = original_dir


def test_get_missingness_rate(temp_config_dir):
    """Test retrieving missingness rate for a specific mechanism."""
    import src.config_loader as config_loader_module
    original_dir = config_loader_module.CONFIG_DIR
    config_loader_module.CONFIG_DIR = temp_config_dir

    try:
        config = load_missingness_config()
        rate = get_missingness_rate('mcar', config)
        assert rate == 0.1
        
        with pytest.raises(ValueError, match="Unknown mechanism"):
            get_missingness_rate('unknown', config)
    finally:
        config_loader_module.CONFIG_DIR = original_dir


def test_load_all_configs(temp_config_dir):
    """Test loading all configurations at once."""
    import src.config_loader as config_loader_module
    original_dir = config_loader_module.CONFIG_DIR
    config_loader_module.CONFIG_DIR = temp_config_dir

    try:
        sim_config, miss_config, est_config = load_all_configs()
        
        assert sim_config['sample_size'] == 500
        assert miss_config['mechanisms'] == ['mcar', 'mar']
        assert est_config['bandwidth_rule'] == 'IK'
    finally:
        config_loader_module.CONFIG_DIR = original_dir