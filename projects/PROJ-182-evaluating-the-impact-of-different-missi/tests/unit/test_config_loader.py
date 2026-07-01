"""
Unit tests for the configuration loader module.
"""
import os
import tempfile
import pytest
import yaml
import sys

# Add the code/src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'src'))

from config_loader import (
    load_simulation_config,
    load_missingness_config,
    load_estimation_config,
    load_all_configs,
    SimulationConfig,
    MissingnessConfig,
    EstimationConfig
)


class TestSimulationConfig:
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid simulation configuration."""
        config_data = {
            'sample_size': 1000,
            'true_effect': 0.5,
            'seed': 42
        }
        
        config_file = tmp_path / "simulation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_simulation_config(str(config_file))
        
        assert config.sample_size == 1000
        assert config.true_effect == 0.5
        assert config.seed == 42
        assert config.beta0 == 0.0
        assert config.beta1 == 1.0
        assert config.beta2 == 0.5
        assert config.sigma == 1.0
    
    def test_load_config_with_optional_fields(self, tmp_path):
        """Test loading simulation config with optional fields."""
        config_data = {
            'sample_size': 500,
            'true_effect': 1.0,
            'seed': 123,
            'beta0': 2.0,
            'beta1': 0.5,
            'beta2': 1.5,
            'sigma': 2.0
        }
        
        config_file = tmp_path / "simulation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_simulation_config(str(config_file))
        
        assert config.sample_size == 500
        assert config.true_effect == 1.0
        assert config.seed == 123
        assert config.beta0 == 2.0
        assert config.beta1 == 0.5
        assert config.beta2 == 1.5
        assert config.sigma == 2.0
    
    def test_missing_required_field(self, tmp_path):
        """Test that missing required fields raise ValueError."""
        config_data = {
            'sample_size': 1000,
            'seed': 42
            # missing 'true_effect'
        }
        
        config_file = tmp_path / "simulation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(ValueError, match="Missing required field"):
            load_simulation_config(str(config_file))
    
    def test_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_simulation_config("non_existent_file.yaml")


class TestMissingnessConfig:
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid missingness configuration."""
        config_data = {
            'rates': {
                'mcar': 0.15,
                'mar': 0.25,
                'mnar': 0.30
            },
            'mechanisms': {
                'mcar': 'completely_at_random',
                'mar': 'at_random',
                'mnar': 'not_at_random'
            }
        }
        
        config_file = tmp_path / "missingness.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_missingness_config(str(config_file))
        
        assert config.rates['mcar'] == 0.15
        assert config.rates['mar'] == 0.25
        assert config.rates['mnar'] == 0.30
        assert config.mechanisms['mcar'] == 'completely_at_random'
        assert config.mechanisms['mar'] == 'at_random'
        assert config.mechanisms['mnar'] == 'not_at_random'
    
    def test_load_config_with_defaults(self, tmp_path):
        """Test loading missingness config with default values."""
        config_data = {}
        
        config_file = tmp_path / "missingness.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_missingness_config(str(config_file))
        
        assert config.rates['mcar'] == 0.2
        assert config.rates['mar'] == 0.2
        assert config.rates['mnar'] == 0.2
    
    def test_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_missingness_config("non_existent_file.yaml")


class TestEstimationConfig:
    def test_load_valid_config(self, tmp_path):
        """Test loading a valid estimation configuration."""
        config_data = {
            'bandwidth_rule': 'ik',
            'imputation_count': 10,
            'nominal_confidence': 0.99,
            'bandwidth_floor': 0.1
        }
        
        config_file = tmp_path / "estimation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_estimation_config(str(config_file))
        
        assert config.bandwidth_rule == 'ik'
        assert config.imputation_count == 10
        assert config.nominal_confidence == 0.99
        assert config.bandwidth_floor == 0.1
    
    def test_load_config_with_defaults(self, tmp_path):
        """Test loading estimation config with default values."""
        config_data = {}
        
        config_file = tmp_path / "estimation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        config = load_estimation_config(str(config_file))
        
        assert config.bandwidth_rule == 'ik'
        assert config.imputation_count == 5
        assert config.nominal_confidence == 0.95
        assert config.bandwidth_floor == 0.05
    
    def test_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_estimation_config("non_existent_file.yaml")


class TestLoadAllConfigs:
    def test_load_all_configs(self, tmp_path):
        """Test loading all configuration files at once."""
        # Create simulation config
        sim_data = {
            'sample_size': 1000,
            'true_effect': 0.5,
            'seed': 42
        }
        sim_file = tmp_path / "simulation.yaml"
        with open(sim_file, 'w') as f:
            yaml.dump(sim_data, f)
        
        # Create missingness config
        miss_data = {
            'rates': {'mcar': 0.1, 'mar': 0.2, 'mnar': 0.3}
        }
        miss_file = tmp_path / "missingness.yaml"
        with open(miss_file, 'w') as f:
            yaml.dump(miss_data, f)
        
        # Create estimation config
        est_data = {
            'bandwidth_rule': 'ik',
            'imputation_count': 5
        }
        est_file = tmp_path / "estimation.yaml"
        with open(est_file, 'w') as f:
            yaml.dump(est_data, f)
        
        sim_cfg, miss_cfg, est_cfg = load_all_configs(
            str(sim_file),
            str(miss_file),
            str(est_file)
        )
        
        assert isinstance(sim_cfg, SimulationConfig)
        assert isinstance(miss_cfg, MissingnessConfig)
        assert isinstance(est_cfg, EstimationConfig)
        
        assert sim_cfg.sample_size == 1000
        assert miss_cfg.rates['mcar'] == 0.1
        assert est_cfg.bandwidth_rule == 'ik'
    
    def test_load_all_configs_missing_file(self, tmp_path):
        """Test that missing a config file raises FileNotFoundError."""
        # Create only simulation config
        sim_data = {
            'sample_size': 1000,
            'true_effect': 0.5,
            'seed': 42
        }
        sim_file = tmp_path / "simulation.yaml"
        with open(sim_file, 'w') as f:
            yaml.dump(sim_data, f)
        
        with pytest.raises(FileNotFoundError):
            load_all_configs(
                str(sim_file),
                "non_existent_missingness.yaml",
                "non_existent_estimation.yaml"
            )