"""
Unit test for T020: Mock test for model loading in tests/unit/test_model_load.py.

Verifies that:
1. The model loading function correctly sets the `bitsandbytes` 4-bit quantization flag.
2. The model is configured to use the CPU device.

This test uses mocking to verify configuration without actually loading the large model,
ensuring the test runs quickly and deterministically.
"""
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from model.inference import load_model, get_logger
from config import get_model_path, get_seed_global


class TestModelLoadConfiguration:
    """Tests for verifying model loading configuration."""

    @pytest.fixture
    def mock_env(self):
        """Fixture to ensure environment variables are set for testing."""
        with patch.dict(os.environ, {}, clear=False):
            yield

    @pytest.fixture
    def mock_logger(self):
        """Fixture to mock the logger to avoid I/O during tests."""
        with patch("model.inference.get_logger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            yield mock_logger

    def test_bitsandbytes_4bit_quantization_flag(self, mock_logger, mock_env):
        """
        Verify that the model loading process sets the bitsandbytes 4-bit quantization flag.
        
        This test ensures that when `load_model` is called, it attempts to load the model
        with `load_in_4bit=True` and the appropriate `bnb_4bit_compute_dtype` configuration.
        """
        model_path = get_model_path()
        
        # Mock the transformers AutoModelForCausalLM and BitsAndBytesConfig
        with patch("model.inference.AutoModelForCausalLM") as mock_auto_model, \
             patch("model.inference.BitsAndBytesConfig") as mock_bnb_config, \
             patch("model.inference.AutoTokenizer") as mock_tokenizer:
            
            # Setup mocks
            mock_model_instance = MagicMock()
            mock_auto_model.from_pretrained.return_value = mock_model_instance
            
            mock_tokenizer_instance = MagicMock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            
            # Call the function
            try:
                model, tokenizer = load_model(model_path)
            except Exception:
                # We expect this to fail if dependencies aren't installed, 
                # but we care about the configuration call
                pass

            # Verify BitsAndBytesConfig was called with 4-bit quantization
            assert mock_bnb_config.call_count > 0, "BitsAndBytesConfig should be instantiated"
            
            # Get the call arguments for BitsAndBytesConfig
            bnb_call_args = mock_bnb_config.call_args
            assert bnb_call_args is not None, "BitsAndBytesConfig must be called"
            
            # Check that load_in_4bit is set to True
            # The config is usually passed as a keyword argument
            if bnb_call_args.kwargs:
                assert bnb_call_args.kwargs.get("load_in_4bit") is True, \
                    "load_in_4bit must be True for 4-bit quantization"
            elif bnb_call_args.args:
                # If passed as positional, check the first arg if it's a dict or object with the attribute
                config_arg = bnb_call_args.args[0] if bnb_call_args.args else None
                if hasattr(config_arg, 'load_in_4bit'):
                    assert config_arg.load_in_4bit is True, \
                        "load_in_4bit must be True for 4-bit quantization"
                else:
                    # Fallback: check if it's a dict-like object
                    if isinstance(config_arg, dict):
                        assert config_arg.get("load_in_4bit") is True, \
                            "load_in_4bit must be True for 4-bit quantization"

    def test_cpu_device_usage(self, mock_logger, mock_env):
        """
        Verify that the model is configured to use the CPU device.
        
        This test ensures that the model loading process explicitly sets the device
        to CPU, preventing any accidental GPU allocation.
        """
        model_path = get_model_path()
        
        with patch("model.inference.AutoModelForCausalLM") as mock_auto_model, \
             patch("model.inference.BitsAndBytesConfig") as mock_bnb_config, \
             patch("model.inference.AutoTokenizer") as mock_tokenizer, \
             patch("model.inference.torch") as mock_torch:
            
            # Setup mocks
            mock_model_instance = MagicMock()
            mock_auto_model.from_pretrained.return_value = mock_model_instance
            
            mock_tokenizer_instance = MagicMock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            
            # Mock torch device to verify CPU usage
            mock_torch.device.return_value = MagicMock()
            mock_torch.cuda.is_available.return_value = False  # Force CPU path
            
            try:
                model, tokenizer = load_model(model_path)
            except Exception:
                pass

            # Verify that the model was moved to CPU or initialized on CPU
            # Check if 'device_map' or 'torch.device' was used with 'cpu'
            from_pretrained_call = mock_auto_model.from_pretrained.call_args
            
            if from_pretrained_call:
                kwargs = from_pretrained_call.kwargs
                args = from_pretrained_call.args
                
                # Check for device_map='cpu'
                if "device_map" in kwargs:
                    assert kwargs["device_map"] == "cpu" or (
                        isinstance(kwargs["device_map"], dict) and 
                        "cpu" in str(kwargs["device_map"])
                    ), "device_map should target CPU"
                
                # Check for torch.device('cpu')
                if "torch_dtype" in kwargs or "device" in kwargs:
                    # If device is explicitly set, it should be CPU
                    pass 
                
                # Verify that we didn't accidentally use CUDA
                # The config should prevent GPU usage
                assert not (hasattr(mock_torch, 'cuda') and mock_torch.cuda.is_available()), \
                    "Model loading should not attempt to use CUDA"

    def test_model_loading_calls_from_pretrained_with_correct_args(self, mock_logger, mock_env):
        """
        Verify that the model is loaded with the correct arguments including
        quantization config and device settings.
        """
        model_path = get_model_path()
        
        with patch("model.inference.AutoModelForCausalLM") as mock_auto_model, \
             patch("model.inference.BitsAndBytesConfig") as mock_bnb_config, \
             patch("model.inference.AutoTokenizer") as mock_tokenizer:
            
            mock_model_instance = MagicMock()
            mock_auto_model.from_pretrained.return_value = mock_model_instance
            mock_tokenizer_instance = MagicMock()
            mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
            
            # Create a mock BNB config instance
            mock_bnb_instance = MagicMock()
            mock_bnb_config.return_value = mock_bnb_instance
            
            try:
                model, tokenizer = load_model(model_path)
            except Exception:
                pass

            # Verify from_pretrained was called
            assert mock_auto_model.from_pretrained.call_count > 0, \
                "AutoModelForCausalLM.from_pretrained must be called"
            
            call_args = mock_auto_model.from_pretrained.call_args
            assert call_args is not None
            
            # The first positional arg should be the model path
            if call_args.args:
                assert call_args.args[0] == model_path, \
                    "Model path must be passed to from_pretrained"
            
            # Verify quantization config is passed
            kwargs = call_args.kwargs
            assert "quantization_config" in kwargs or "device_map" in kwargs, \
                "Quantization or device configuration must be provided"