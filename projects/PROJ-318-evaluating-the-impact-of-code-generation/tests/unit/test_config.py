"""
Unit tests for the configuration and environment management module.
"""
import pytest
import torch
import os
from unittest.mock import patch, MagicMock

# Import the module under test
from code.utils.config import (
    get_device_and_dtype, 
    validate_model_path, 
    get_quantization_config,
    RAM_LIMIT_GB
)

class TestGetDeviceAndDtype:
    def test_cuda_available(self):
        """Test that CUDA device is returned when available."""
        with patch('torch.cuda.is_available', return_value=True):
            device, dtype = get_device_and_dtype()
            assert device.type == 'cuda'
            assert dtype == torch.float16

    def test_cuda_unavailable_cpu_fallback(self):
        """Test that CPU device and float32 are returned when CUDA is unavailable."""
        with patch('torch.cuda.is_available', return_value=False):
            device, dtype = get_device_and_dtype()
            assert device.type == 'cpu'
            assert dtype == torch.float32

class TestValidateModelPath:
    def test_valid_path(self):
        """Test validation of a standard HuggingFace path."""
        assert validate_model_path("Salesforce/codegen-350M-mono") is True

    def test_empty_path_raises(self):
        """Test that an empty path raises ValueError."""
        with pytest.raises(ValueError):
            validate_model_path("")

    def test_none_path_raises(self):
        """Test that a None path raises ValueError."""
        with pytest.raises(ValueError):
            validate_model_path(None)

    def test_invalid_type_raises(self):
        """Test that non-string path raises ValueError."""
        with pytest.raises(ValueError):
            validate_model_path(123)

class TestGetQuantizationConfig:
    def test_cuda_available_returns_config(self):
        """Test that quantization config is returned when CUDA is available."""
        with patch('torch.cuda.is_available', return_value=True):
            config = get_quantization_config()
            assert config is not None
            assert config["load_in_4bit"] is True

    def test_cuda_unavailable_returns_none(self):
        """Test that None is returned when CUDA is unavailable."""
        with patch('torch.cuda.is_available', return_value=False):
            config = get_quantization_config()
            assert config is None
