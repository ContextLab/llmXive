"""
Unit tests for the configuration management module.

Tests verify that:
- Default values are correctly set
- Environment variables override defaults
- YAML config files are loaded correctly
- Random seeding works as expected
- Configuration persistence works
"""
import os
import pytest
import random
import numpy as np
from pathlib import Path
import tempfile
import yaml
from src.lib.config import (
    Config,
    get_config,
    reset_config,
    set_seed,
    DEFAULT_SEED,
    DEFAULT_GRID_RES,
    DEFAULT_SAMPLE_SIZE,
    DEFAULT_PERMUTATIONS
)

class TestConfigDefaults:
    """Test that default configuration values are correctly set."""
    
    def test_default_seed(self):
        """Test that default seed is 42."""
        config = Config()
        assert config.seed == DEFAULT_SEED
        assert config.seed == 42
    
    def test_default_grid_res(self):
        """Test that default grid resolution is 0.5."""
        config = Config()
        assert config.grid_res == DEFAULT_GRID_RES
        assert config.grid_res == 0.5
    
    def test_default_sample_size(self):
        """Test that default sample size is None."""
        config = Config()
        assert config.sample_size is None
    
    def test_default_permutations(self):
        """Test that default permutations is 10000."""
        config = Config()
        assert config.permutations == DEFAULT_PERMUTATIONS
        assert config.permutations == 10000
    
    def test_default_config_repr(self):
        """Test string representation of default config."""
        config = Config()
        expected = (
            f"Config(seed=42, grid_res=0.5, "
            f"sample_size=None, permutations=10000)"
        )
        assert repr(config) == expected

class TestConfigEnvironmentVariables:
    """Test that environment variables correctly override defaults."""
    
    def setup_method(self):
        """Save original environment variables."""
        self.original_env = {
            'SEED': os.environ.get('SEED'),
            'GRID_RES': os.environ.get('GRID_RES'),
            'SAMPLE_SIZE': os.environ.get('SAMPLE_SIZE'),
            'PERMUTATIONS': os.environ.get('PERMUTATIONS')
        }
    
    def teardown_method(self):
        """Restore original environment variables."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        
        # Reset global config to force re-reading env vars
        reset_config()
    
    def test_seed_from_env(self):
        """Test that SEED environment variable is read."""
        os.environ['SEED'] = '123'
        config = Config()
        assert config.seed == 123
    
    def test_grid_res_from_env(self):
        """Test that GRID_RES environment variable is read."""
        os.environ['GRID_RES'] = '1.0'
        config = Config()
        assert config.grid_res == 1.0
    
    def test_sample_size_from_env(self):
        """Test that SAMPLE_SIZE environment variable is read."""
        os.environ['SAMPLE_SIZE'] = '5000'
        config = Config()
        assert config.sample_size == 5000
    
    def test_permutations_from_env(self):
        """Test that PERMUTATIONS environment variable is read."""
        os.environ['PERMUTATIONS'] = '50000'
        config = Config()
        assert config.permutations == 50000
    
    def test_explicit_args_override_env(self):
        """Test that explicit arguments override environment variables."""
        os.environ['SEED'] = '100'
        config = Config(seed=200)
        assert config.seed == 200

class TestConfigMethods:
    """Test configuration methods and utilities."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config(seed=99, grid_res=0.25, sample_size=1000, permutations=5000)
        result = config.to_dict()
        assert result == {
            'seed': 99,
            'grid_res': 0.25,
            'sample_size': 1000,
            'permutations': 5000
        }
    
    def test_to_yaml(self):
        """Test conversion to YAML string."""
        config = Config(seed=42, grid_res=0.5)
        yaml_str = config.to_yaml()
        assert 'seed: 42' in yaml_str
        assert 'grid_res: 0.5' in yaml_str
        assert 'permutations: 10000' in yaml_str
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config = Config(seed=123, grid_res=0.75, sample_size=2000, permutations=20000)
        config_path = tmp_path / "test_config.yaml"
        
        config.save(config_path)
        
        loaded_config = Config.load(config_path)
        
        assert loaded_config.seed == 123
        assert loaded_config.grid_res == 0.75
        assert loaded_config.sample_size == 2000
        assert loaded_config.permutations == 20000
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading from a non-existent file uses defaults."""
        config_path = tmp_path / "nonexistent.yaml"
        config = Config.load(config_path)
        
        assert config.seed == DEFAULT_SEED
        assert config.grid_res == DEFAULT_GRID_RES
    
    def test_equality(self):
        """Test configuration equality."""
        config1 = Config(seed=42, grid_res=0.5)
        config2 = Config(seed=42, grid_res=0.5)
        config3 = Config(seed=43, grid_res=0.5)
        
        assert config1 == config2
        assert config1 != config3
        assert config1 != "not a config"
    
    def test_apply_seed_to_random(self):
        """Test that seed is applied to random number generators."""
        config1 = Config(seed=100)
        val1 = random.random()
        np_val1 = np.random.random()
        
        config2 = Config(seed=100)
        val2 = random.random()
        np_val2 = np.random.random()
        
        assert val1 == val2
        assert np_val1 == np_val2
    
    def test_different_seeds_produce_different_values(self):
        """Test that different seeds produce different random values."""
        config1 = Config(seed=100)
        val1 = random.random()
        
        config2 = Config(seed=200)
        val2 = random.random()
        
        assert val1 != val2

class TestGlobalConfig:
    """Test global configuration management."""
    
    def setup_method(self):
        """Reset global config before each test."""
        reset_config()
    
    def teardown_method(self):
        """Reset global config after each test."""
        reset_config()
    
    def test_get_config_returns_instance(self):
        """Test that get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)
    
    def test_get_config_returns_same_instance(self):
        """Test that get_config returns the same instance on multiple calls."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_get_config_with_path(self, tmp_path):
        """Test that get_config with path creates new instance."""
        config_path = tmp_path / "test.yaml"
        Config(seed=999).save(config_path)
        
        config = get_config(config_path=config_path)
        assert config.seed == 999
        
        # Subsequent calls without path should return the same instance
        config2 = get_config()
        assert config2 is config
    
    def test_reset_config(self):
        """Test that reset_config forces re-initialization."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        
        # They should be different instances
        assert config1 is not config2
    
    def test_set_seed_updates_global(self):
        """Test that set_seed updates the global configuration."""
        get_config()  # Initialize global
        set_seed(999)
        
        config = get_config()
        assert config.seed == 999
    
    def test_set_seed_affects_random(self):
        """Test that set_seed affects random number generation."""
        get_config()
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

class TestConfigEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_yaml_file(self, tmp_path):
        """Test loading from an empty YAML file."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")
        
        config = Config.load(config_path)
        assert config.seed == DEFAULT_SEED
    
    def test_yaml_with_missing_keys(self, tmp_path):
        """Test loading from YAML with some keys missing."""
        config_path = tmp_path / "partial.yaml"
        config_path.write_text("seed: 123\n")
        
        config = Config.load(config_path)
        assert config.seed == 123
        assert config.grid_res == DEFAULT_GRID_RES
        assert config.permutations == DEFAULT_PERMUTATIONS
    
    def test_invalid_seed_type(self):
        """Test that seed is converted to int."""
        config = Config(seed="42")
        assert isinstance(config.seed, int)
        assert config.seed == 42
    
    def test_invalid_grid_res_type(self):
        """Test that grid_res is converted to float."""
        config = Config(grid_res="0.5")
        assert isinstance(config.grid_res, float)
        assert config.grid_res == 0.5
    
    def test_invalid_permutations_type(self):
        """Test that permutations is converted to int."""
        config = Config(permutations="10000")
        assert isinstance(config.permutations, int)
        assert config.permutations == 10000

class TestIntegrationWithPipeline:
    """Test configuration integration with pipeline components."""
    
    def test_config_used_in_preprocessing(self):
        """Test that config can be used for grid resolution."""
        config = get_config()
        assert config.grid_res == 0.5
        # This would be used in preprocess.py for grid assignment
    
    def test_config_used_in_permutation_tests(self):
        """Test that config provides permutation count."""
        config = get_config()
        assert config.permutations == 10000
        # This would be used in utils.py for permutation tests
    
    def test_reproducible_pipeline(self):
        """Test that same config produces reproducible results."""
        # Set up config
        config1 = Config(seed=42)
        random.seed(config1.seed)
        np.random.seed(config1.seed)
        result1 = (random.random(), np.random.random())
        
        # Reset and use same seed
        config2 = Config(seed=42)
        random.seed(config2.seed)
        np.random.seed(config2.seed)
        result2 = (random.random(), np.random.random())
        
        assert result1 == result2

# Additional tests for specific task requirements
class TestTaskRequirements:
    """Tests specifically for T011 requirements."""
    
    def test_seed_default_is_42(self):
        """Verify SEED=42 as specified in T011."""
        config = Config()
        assert config.seed == 42
    
    def test_grid_res_default_is_0_5(self):
        """Verify GRID_RES=0.5 as specified in T011 (linked to T015)."""
        config = Config()
        assert config.grid_res == 0.5
    
    def test_permutations_default_is_10000(self):
        """Verify PERMUTATIONS=10000 as specified in T011."""
        config = Config()
        assert config.permutations == 10000
    
    def test_sample_size_exists(self):
        """Verify SAMPLE_SIZE variable exists."""
        config = Config()
        assert hasattr(config, 'sample_size')
    
    def test_all_variables_are_accessible(self):
        """Verify all required variables are accessible."""
        config = Config()
        assert hasattr(config, 'seed')
        assert hasattr(config, 'grid_res')
        assert hasattr(config, 'sample_size')
        assert hasattr(config, 'permutations')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
