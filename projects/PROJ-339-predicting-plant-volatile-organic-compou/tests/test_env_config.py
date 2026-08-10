"""
Tests for environment variable management configuration.

These tests verify that the EnvConfig class correctly:
1. Loads environment variables from .env file
2. Provides typed accessors for paths and seeds
3. Validates directory existence
4. Handles configuration errors appropriately
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.env_config import (
    EnvConfig,
    EnvConfigError,
    get_config,
    reset_config
)


class TestEnvConfig:
    """Test suite for EnvConfig class."""
    
    def test_default_initialization(self, tmp_path):
        """Test that default values are set correctly when env vars are missing."""
        # Create a temporary directory structure
        with patch.dict(os.environ, {}, clear=True):
            with patch('pathlib.Path.exists', return_value=True):
                config = EnvConfig()
                
                assert config.random_seed == 42
                assert config.n_jobs == -1
                assert config.verbose is False
                
                # Check that paths are set (they will be mocked to exist)
                assert config.data_root is not None
                assert config.data_raw is not None
    
    def test_custom_seed(self):
        """Test that custom random seed is loaded from environment."""
        with patch.dict(os.environ, {'RANDOM_SEED': '123'}):
            with patch('pathlib.Path.exists', return_value=True):
                config = EnvConfig()
                assert config.random_seed == 123
    
    def test_custom_n_jobs(self):
        """Test that custom n_jobs is loaded from environment."""
        with patch.dict(os.environ, {'N_JOBS': '4'}):
            with patch('pathlib.Path.exists', return_value=True):
                config = EnvConfig()
                assert config.n_jobs == 4
    
    def test_verbose_true(self):
        """Test that verbose flag is correctly parsed."""
        with patch.dict(os.environ, {'VERBOSE': 'true'}):
            with patch('pathlib.Path.exists', return_value=True):
                config = EnvConfig()
                assert config.verbose is True
    
    def test_verbose_false(self):
        """Test that verbose flag defaults to False."""
        with patch.dict(os.environ, {'VERBOSE': 'false'}):
            with patch('pathlib.Path.exists', return_value=True):
                config = EnvConfig()
                assert config.verbose is False
    
    def test_path_getter(self):
        """Test that get_path returns correct directories."""
        with patch('pathlib.Path.exists', return_value=True):
            config = EnvConfig()
            
            assert config.get_path('data_raw') == config.data_raw
            assert config.get_path('data_processed') == config.data_processed
            assert config.get_path('data_results') == config.data_results
            assert config.get_path('data_models') == config.data_models
            assert config.get_path('specs') == config.specs_root
    
    def test_invalid_path_key(self):
        """Test that invalid path key raises EnvConfigError."""
        with patch('pathlib.Path.exists', return_value=True):
            config = EnvConfig()
            
            with pytest.raises(EnvConfigError, match="Unknown path key"):
                config.get_path('invalid_key')
    
    def test_to_dict(self):
        """Test that configuration can be converted to dictionary."""
        with patch('pathlib.Path.exists', return_value=True):
            config = EnvConfig()
            config_dict = config.to_dict()
            
            assert 'project_root' in config_dict
            assert 'data_root' in config_dict
            assert 'random_seed' in config_dict
            assert 'n_jobs' in config_dict
            assert 'verbose' in config_dict
            assert isinstance(config_dict['random_seed'], int)
    
    def test_save_and_load_json(self, tmp_path):
        """Test saving and loading configuration from JSON file."""
        with patch('pathlib.Path.exists', return_value=True):
            config = EnvConfig()
            
            # Save to JSON
            json_path = tmp_path / 'config.json'
            config.save_to_json(json_path)
            
            assert json_path.exists()
            
            # Load from JSON
            loaded_config = EnvConfig.from_json(json_path)
            
            assert loaded_config.random_seed == config.random_seed
            assert loaded_config.n_jobs == config.n_jobs
            assert loaded_config.verbose == config.verbose
    
    def test_missing_directory_validation(self):
        """Test that missing required directories raise EnvConfigError."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(EnvConfigError, match="Required directory does not exist"):
                EnvConfig()
    
    def test_singleton_pattern(self):
        """Test that get_config returns the same instance."""
        reset_config()
        
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2
    
    def test_reset_config(self):
        """Test that reset_config clears the singleton instance."""
        reset_config()
        config1 = get_config()
        
        reset_config()
        config2 = get_config()
        
        assert config1 is not config2


class TestEnvConfigIntegration:
    """Integration tests for environment configuration."""
    
    def test_env_file_loading(self, tmp_path):
        """Test that .env file is loaded correctly."""
        env_content = """
        RANDOM_SEED=999
        N_JOBS=2
        VERBOSE=true
        """
        
        env_file = tmp_path / '.env'
        env_file.write_text(env_content)
        
        # Create required directories
        data_root = tmp_path / 'data'
        data_root.mkdir()
        (data_root / 'raw').mkdir()
        (data_root / 'processed').mkdir()
        (data_root / 'results').mkdir()
        (data_root / 'models').mkdir()
        (tmp_path / 'specs').mkdir()
        
        with patch.dict(os.environ, {'PROJECT_ROOT': str(tmp_path)}):
            with patch('utils.env_config.load_dotenv') as mock_load_dotenv:
                # Mock load_dotenv to actually read our file
                from dotenv import load_dotenv as real_load_dotenv
                real_load_dotenv(env_file)
                
                config = EnvConfig()
                
                assert config.random_seed == 999
                assert config.n_jobs == 2
                assert config.verbose is True
    
    def test_path_construction(self, tmp_path):
        """Test that paths are constructed correctly from environment."""
        data_root = tmp_path / 'custom_data'
        data_root.mkdir()
        (data_root / 'raw').mkdir()
        (data_root / 'processed').mkdir()
        (data_root / 'results').mkdir()
        (data_root / 'models').mkdir()
        (tmp_path / 'custom_specs').mkdir()
        
        with patch.dict(os.environ, {
            'PROJECT_ROOT': str(tmp_path),
            'DATA_ROOT': str(data_root),
            'SPECS_ROOT': str(tmp_path / 'custom_specs')
        }):
            with patch('pathlib.Path.exists', return_value=True):
                config = EnvConfig()
                
                assert config.data_root == data_root
                assert config.specs_root == tmp_path / 'custom_specs'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
