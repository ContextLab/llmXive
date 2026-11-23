"""
Unit tests for CPU-only environment configuration.

Tests verify that:
1. Environment variables are set correctly for CPU-only execution
2. PyTorch is configured to use CPU only
3. Validation functions work correctly
4. Configuration functions return expected values
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, 'code')

from setup_cpu_env import (
    set_cpu_only_environment,
    validate_cpu_only_environment,
    get_cpu_config,
    configure_pytorch_cpu_only,
    configure_transformers_cpu_only,
    configure_sentence_transformers_cpu_only,
    verify_cpu_constraints,
    CPU_ONLY_ENV_VARS,
)


class TestSetCpuOnlyEnvironment:
    """Tests for set_cpu_only_environment function."""
    
    def test_sets_all_cpu_only_env_vars(self):
        """Test that all CPU-only environment variables are set."""
        result = set_cpu_only_environment()
        
        for var, expected_value in CPU_ONLY_ENV_VARS.items():
            assert os.environ.get(var) == expected_value
            assert var in result
            assert result[var] == expected_value
    
    def test_overwrites_existing_gpu_vars(self):
        """Test that existing GPU-related variables are overwritten."""
        # Set a GPU-related variable
        os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'
        
        result = set_cpu_only_environment()
        
        assert os.environ['CUDA_VISIBLE_DEVICES'] == '-1'
        assert result['CUDA_VISIBLE_DEVICES'] == '-1'
    
    def test_returns_dict_of_set_variables(self):
        """Test that the function returns a dictionary of set variables."""
        result = set_cpu_only_environment()
        
        assert isinstance(result, dict)
        assert len(result) == len(CPU_ONLY_ENV_VARS)
        assert set(result.keys()) == set(CPU_ONLY_ENV_VARS.keys())


class TestValidateCpuOnlyEnvironment:
    """Tests for validate_cpu_only_environment function."""
    
    @patch('os.environ.get')
    def test_returns_true_when_cuda_disabled(self, mock_get):
        """Test validation returns True when CUDA is disabled."""
        mock_get.return_value = '-1'
        
        # Mock torch.cuda.is_available to return False
        with patch('setup_cpu_env.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            
            result = validate_cpu_only_environment()
            
            assert result is True
    
    @patch('os.environ.get')
    def test_returns_false_when_cuda_enabled(self, mock_get):
        """Test validation returns False when CUDA is enabled."""
        mock_get.return_value = '0'
        
        result = validate_cpu_only_environment()
        
        assert result is False
    
    def test_handles_missing_torch(self):
        """Test validation handles missing PyTorch gracefully."""
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        
        with patch.dict('sys.modules', {'torch': None}):
            # Should not raise an exception
            result = validate_cpu_only_environment()
            
            # Should return True if environment is configured correctly
            assert result is True
    
    @patch('os.environ.get')
    def test_validates_cuda_visible_devices(self, mock_get):
        """Test that CUDA_VISIBLE_DEVICES is validated correctly."""
        mock_get.side_effect = lambda key, default='': '-1' if key == 'CUDA_VISIBLE_DEVICES' else default
        
        with patch('setup_cpu_env.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            
            result = validate_cpu_only_environment()
            
            assert result is True
    
    @patch('os.environ.get')
    def test_fails_on_positive_cuda_visible_devices(self, mock_get):
        """Test validation fails when CUDA_VISIBLE_DEVICES is positive."""
        mock_get.side_effect = lambda key, default='': '0' if key == 'CUDA_VISIBLE_DEVICES' else default
        
        result = validate_cpu_only_environment()
        
        assert result is False


class TestGetCpuConfig:
    """Tests for get_cpu_config function."""
    
    def test_returns_cpu_config_dict(self):
        """Test that get_cpu_config returns the correct configuration."""
        config = get_cpu_config()
        
        assert config['device'] == 'cpu'
        assert config['num_workers'] == 0
        assert config['pin_memory'] is False
        assert config['cuda'] is False
        assert config['mps'] is False
        assert config['xla'] is False
    
    def test_all_values_are_correct_types(self):
        """Test that all configuration values are of correct types."""
        config = get_cpu_config()
        
        assert isinstance(config['device'], str)
        assert isinstance(config['num_workers'], int)
        assert isinstance(config['pin_memory'], bool)
        assert isinstance(config['cuda'], bool)
        assert isinstance(config['mps'], bool)
        assert isinstance(config['xla'], bool)


class TestConfigurePytorchCpuOnly:
    """Tests for configure_pytorch_cpu_only function."""
    
    @patch('setup_cpu_env.torch')
    def test_configures_torch_for_cpu(self, mock_torch):
        """Test that PyTorch is configured for CPU-only."""
        mock_torch.cuda.is_available.return_value = False
        
        configure_pytorch_cpu_only()
        
        mock_torch.set_default_device.assert_called_with('cpu')
        assert not mock_torch.backends.cudnn.enabled
        assert mock_torch.set_num_threads.called
    
    @patch('setup_cpu_env.torch')
    def test_handles_cuda_warning(self, mock_torch):
        """Test that a warning is logged when CUDA is available."""
        mock_torch.cuda.is_available.return_value = True
        
        # Should not raise an exception
        configure_pytorch_cpu_only()
        
        assert mock_torch.backends.cudnn.enabled is False
    
    def test_handles_missing_torch(self):
        """Test that the function handles missing PyTorch gracefully."""
        with patch.dict('sys.modules', {'torch': None}):
            # Should not raise an exception
            configure_pytorch_cpu_only()

class TestVerifyCpuConstraints:
    """Tests for verify_cpu_constraints function."""
    
    @patch('setup_cpu_env.set_cpu_only_environment')
    @patch('setup_cpu_env.validate_cpu_only_environment')
    def test_returns_verification_results(self, mock_validate, mock_set_env):
        """Test that verify_cpu_constraints returns the expected structure."""
        mock_set_env.return_value = {'CUDA_VISIBLE_DEVICES': '-1'}
        mock_validate.return_value = True
        
        with patch('setup_cpu_env.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            with patch('setup_cpu_env.transformers'):
                with patch('setup_cpu_env.sentence_transformers'):
                    result = verify_cpu_constraints()
                    
                    assert 'cpu_only' in result
                    assert 'environment_configured' in result
                    assert 'pytorch_configured' in result
                    assert 'transformers_configured' in result
                    assert 'sentence_transformers_configured' in result
                    assert 'details' in result
                    
                    assert isinstance(result['cpu_only'], bool)
                    assert isinstance(result['details'], list)
    
    @patch('setup_cpu_env.set_cpu_only_environment')
    @patch('setup_cpu_env.validate_cpu_only_environment')
    def test_sets_cpu_only_false_on_validation_failure(self, mock_validate, mock_set_env):
        """Test that cpu_only is False when validation fails."""
        mock_set_env.return_value = {'CUDA_VISIBLE_DEVICES': '-1'}
        mock_validate.return_value = False
        
        result = verify_cpu_constraints()
        
        assert result['cpu_only'] is False
        assert result['environment_configured'] is False