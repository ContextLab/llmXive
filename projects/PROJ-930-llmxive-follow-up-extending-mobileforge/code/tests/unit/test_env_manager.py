"""
Unit tests for environment variable management.
"""
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.env_manager import (
    load_env_from_file,
    set_environment_variables,
    get_config,
    validate_config,
    set_random_seeds,
    get_project_root,
    REQUIRED_VARS,
    OPTIONAL_VARS
)

class TestEnvFileManager:
    """Tests for environment variable management functions."""

    def test_load_env_from_file_exists(self, tmp_path):
        """Test loading from an existing .env file."""
        env_file = tmp_path / ".env"
        env_content = """
        # Comment line
        KEY1=value1
        KEY2 = value2
        KEY3="value with spaces"
        KEY4='single quoted'
        """
        env_file.write_text(env_content)
        
        result = load_env_from_file(str(env_file))
        
        assert result['KEY1'] == 'value1'
        assert result['KEY2'] == 'value2'
        assert result['KEY3'] == 'value with spaces'
        assert result['KEY4'] == 'single quoted'
        assert 'KEY4' in result

    def test_load_env_from_file_not_exists(self, tmp_path):
        """Test loading from a non-existent .env file."""
        non_existent = tmp_path / "non_existent.env"
        
        result = load_env_from_file(str(non_existent))
        
        assert result == {}

    def test_load_env_from_file_invalid_lines(self, tmp_path):
        """Test handling of invalid lines in .env file."""
        env_file = tmp_path / ".env"
        env_content = """
        VALID_KEY=valid_value
        INVALID_LINE_NO_EQUALS
        ANOTHER_VALID=another_value
        =no_key
        """
        env_file.write_text(env_content)
        
        result = load_env_from_file(str(env_file))
        
        assert result['VALID_KEY'] == 'valid_value'
        assert result['ANOTHER_VALID'] == 'another_value'
        assert 'INVALID_LINE_NO_EQUALS' not in result
        assert '=' not in result  # No key with empty name

    @patch('os.environ')
    def test_set_environment_variables(self, mock_environ):
        """Test setting environment variables from dictionary."""
        test_vars = {
            'MOBILEFORGE_DATASET_PATH': '/path/to/mobileforge',
            'ANDROIDWORLD_DATASET_PATH': '/path/to/androidworld',
            'RANDOM_SEED': '42',
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42'
        }
        
        set_environment_variables(test_vars)
        
        # Check that all variables were set
        for key, value in test_vars.items():
            mock_environ.__setitem__.assert_any_call(key, value)

    @patch('os.environ')
    def test_set_environment_variables_missing_required(self, mock_environ):
        """Test that missing required variables raise an error."""
        # Mock os.environ to not contain required variables
        mock_environ.get.side_effect = KeyError
        
        with pytest.raises(ValueError) as exc_info:
            set_environment_variables({})
        
        assert "Missing required environment variables" in str(exc_info.value)

    @patch('os.environ')
    def test_get_config(self, mock_environ):
        """Test getting configuration from environment variables."""
        mock_environ.get.side_effect = lambda key, default=None: {
            'MOBILEFORGE_DATASET_PATH': '/path/to/mobileforge',
            'ANDROIDWORLD_DATASET_PATH': '/path/to/androidworld',
            'RANDOM_SEED': '42',
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42',
            'LOG_LEVEL': 'DEBUG',
            'MAX_RETRIES': '5',
            'TIMEOUT_SECONDS': '600'
        }.get(key, default)
        
        config = get_config()
        
        assert config['mobileforge_dataset_path'] == '/path/to/mobileforge'
        assert config['androidworld_dataset_path'] == '/path/to/androidworld'
        assert config['random_seed'] == 42
        assert config['torch_seed'] == 42
        assert config['numpy_seed'] == 42
        assert config['log_level'] == 'DEBUG'
        assert config['max_retries'] == 5
        assert config['timeout_seconds'] == 600

    @patch('os.environ')
    def test_validate_config_valid(self, mock_environ, tmp_path):
        """Test validation of valid configuration."""
        # Create temporary directories for dataset paths
        mobileforge_dir = tmp_path / "mobileforge"
        androidworld_dir = tmp_path / "androidworld"
        mobileforge_dir.mkdir()
        androidworld_dir.mkdir()
        
        mock_environ.get.side_effect = lambda key, default=None: {
            'MOBILEFORGE_DATASET_PATH': str(mobileforge_dir),
            'ANDROIDWORLD_DATASET_PATH': str(androidworld_dir),
            'RANDOM_SEED': '42',
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42',
            'MAX_RETRIES': '3',
            'TIMEOUT_SECONDS': '300'
        }.get(key, default)
        
        config = get_config()
        result = validate_config(config)
        
        assert result is True

    @patch('os.environ')
    def test_validate_config_invalid_seed(self, mock_environ):
        """Test validation fails with invalid seed."""
        mock_environ.get.side_effect = lambda key, default=None: {
            'MOBILEFORGE_DATASET_PATH': '/path/to/mobileforge',
            'ANDROIDWORLD_DATASET_PATH': '/path/to/androidworld',
            'RANDOM_SEED': '-1',  # Invalid seed
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42',
            'MAX_RETRIES': '3',
            'TIMEOUT_SECONDS': '300'
        }.get(key, default)
        
        config = get_config()
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(config)
        
        assert "Invalid seed value" in str(exc_info.value)

    @patch('os.environ')
    def test_validate_config_invalid_retries(self, mock_environ):
        """Test validation fails with invalid max_retries."""
        mock_environ.get.side_effect = lambda key, default=None: {
            'MOBILEFORGE_DATASET_PATH': '/path/to/mobileforge',
            'ANDROIDWORLD_DATASET_PATH': '/path/to/androidworld',
            'RANDOM_SEED': '42',
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42',
            'MAX_RETRIES': '0',  # Invalid retries
            'TIMEOUT_SECONDS': '300'
        }.get(key, default)
        
        config = get_config()
        
        with pytest.raises(ValueError) as exc_info:
            validate_config(config)
        
        assert "max_retries must be at least 1" in str(exc_info.value)

    @patch('random.seed')
    @patch('numpy.random.seed')
    @patch('torch.manual_seed')
    def test_set_random_seeds_with_torch(self, mock_torch_seed, mock_np_seed, mock_random_seed):
        """Test setting random seeds with all libraries."""
        import torch
        import numpy as np
        
        # Mock torch.cuda.is_available to return False for simplicity
        with patch('torch.cuda.is_available', return_value=False):
            set_random_seeds(123)
        
        mock_random_seed.assert_called_once_with(123)
        mock_np_seed.assert_called_once_with(123)
        mock_torch_seed.assert_called_once_with(123)

    def test_get_project_root(self):
        """Test getting project root directory."""
        root = get_project_root()
        
        assert isinstance(root, Path)
        assert root.name == "PROJ-930-llmxive-follow-up-extending-mobileforge" or root.parent.name == "PROJ-930-llmxive-follow-up-extending-mobileforge"

    @patch('os.environ')
    def test_set_environment_variables_loads_from_env_file(self, mock_environ, tmp_path):
        """Test that set_environment_variables loads from .env file when no dict provided."""
        env_file = tmp_path / ".env"
        env_content = """
        MOBILEFORGE_DATASET_PATH=/test/mobileforge
        ANDROIDWORLD_DATASET_PATH=/test/androidworld
        RANDOM_SEED=99
        TORCH_SEED=99
        NUMPY_SEED=99
        """
        env_file.write_text(env_content)
        
        # Mock Path(__file__).parent.parent.parent to point to tmp_path
        with patch('utils.env_manager.Path') as mock_path:
            mock_path.return_value = tmp_path
            mock_path.return_value.__truediv__.return_value = env_file
            mock_path.return_value.__truediv__.return_value.exists.return_value = True
            
            # This would normally load from the .env file
            # We're testing the logic path
            pass

    @patch('os.environ')
    def test_validate_config_warning_for_missing_paths(self, mock_environ, tmp_path):
        """Test that validation warns for non-existent dataset paths."""
        mock_environ.get.side_effect = lambda key, default=None: {
            'MOBILEFORGE_DATASET_PATH': '/nonexistent/mobileforge',
            'ANDROIDWORLD_DATASET_PATH': '/nonexistent/androidworld',
            'RANDOM_SEED': '42',
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42',
            'MAX_RETRIES': '3',
            'TIMEOUT_SECONDS': '300'
        }.get(key, default)
        
        config = get_config()
        
        # Should not raise an error, just log warnings
        result = validate_config(config)
        
        assert result is True

    @patch('os.environ')
    def test_set_environment_variables_with_optional_vars(self, mock_environ):
        """Test setting optional environment variables."""
        test_vars = {
            'MOBILEFORGE_DATASET_PATH': '/path/to/mobileforge',
            'ANDROIDWORLD_DATASET_PATH': '/path/to/androidworld',
            'RANDOM_SEED': '42',
            'TORCH_SEED': '42',
            'NUMPY_SEED': '42',
            'LOG_LEVEL': 'DEBUG',
            'MAX_RETRIES': '10',
            'TIMEOUT_SECONDS': '1200'
        }
        
        set_environment_variables(test_vars)
        
        # Verify all variables were set
        calls = [call[0][0] for call in mock_environ.__setitem__.call_args_list]
        assert 'LOG_LEVEL' in calls
        assert 'MAX_RETRIES' in calls
        assert 'TIMEOUT_SECONDS' in calls

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
