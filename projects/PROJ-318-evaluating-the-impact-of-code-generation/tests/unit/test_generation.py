"""
Unit tests for model loading with 4-bit quantization and abort logic.
Tests for T021 [US2].
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.model_loader import ModelLoadException, ModelDeviationException, load_model
from utils.config import get_quantization_config
from utils.monitor import MemoryLimitException
import torch


class TestModelLoading4Bit(unittest.TestCase):
    """Tests for 4-bit quantization enforcement and abort logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_model_path = "Salesforce/codegen-350M-mono"
        self.mock_tokenizer = MagicMock()
        self.mock_model = MagicMock()
        
        # Mock torch.cuda and related functions
        self.cuda_available_patcher = patch('torch.cuda.is_available', return_value=False)
        self.cuda_available_patcher.start()
        
        self.device_patcher = patch('torch.device')
        self.device_mock = self.device_patcher.start()
        self.device_mock.return_value = "cpu"

    def tearDown(self):
        """Clean up test fixtures."""
        self.cuda_available_patcher.stop()
        self.device_patcher.stop()

    @patch('utils.model_loader.AutoTokenizer.from_pretrained')
    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    def test_load_model_with_4bit_quantization(self, mock_from_pretrained, mock_tokenizer):
        """Test that model loads successfully with 4-bit quantization config."""
        # Setup mocks
        mock_tokenizer.return_value = self.mock_tokenizer
        mock_from_pretrained.return_value = self.mock_model
        
        # Create expected quantization config
        expected_config = get_quantization_config(4)
        
        # Call function under test
        model, tokenizer = load_model(self.mock_model_path, device="cpu")
        
        # Verify tokenizer was called
        mock_tokenizer.assert_called_once_with(self.mock_model_path, trust_remote_code=True)
        
        # Verify model was called with 4-bit quantization config
        mock_from_pretrained.assert_called_once()
        call_kwargs = mock_from_pretrained.call_args[1]
        self.assertIn('quantization_config', call_kwargs)
        self.assertIsNotNone(call_kwargs['quantization_config'])
        self.assertEqual(call_kwargs['quantization_config'].bnb_4bit_compute_dtype, torch.float32)
        
        # Verify return values
        self.assertEqual(model, self.mock_model)
        self.assertEqual(tokenizer, self.mock_tokenizer)

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    def test_load_model_aborts_on_quantization_failure(self, mock_from_pretrained):
        """Test that ModelLoadException is raised when quantization fails."""
        # Simulate quantization failure
        mock_from_pretrained.side_effect = ModelLoadException("Quantization failed")
        
        # Verify exception is raised
        with self.assertRaises(ModelLoadException) as context:
            load_model(self.mock_model_path, device="cpu")
        
        self.assertIn("Quantization failed", str(context.exception))

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    def test_load_model_aborts_on_memory_limit(self, mock_from_pretrained):
        """Test that MemoryLimitException is raised when memory limit is exceeded."""
        # Setup mock to raise MemoryLimitException
        mock_from_pretrained.side_effect = MemoryLimitException("Memory limit exceeded")
        
        # Verify exception is raised
        with self.assertRaises(MemoryLimitException) as context:
            load_model(self.mock_model_path, device="cpu")
        
        self.assertIn("Memory limit exceeded", str(context.exception))

    def test_quantization_config_creation(self):
        """Test that 4-bit quantization config is created correctly."""
        config = get_quantization_config(4)
        
        self.assertIsNotNone(config)
        self.assertTrue(config.bnb_4bit_quant_type == "nf4")
        self.assertTrue(config.bnb_4bit_compute_dtype == torch.float32)
        self.assertTrue(config.llm_int8_skip_modules is None)

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    def test_load_model_with_invalid_device(self, mock_from_pretrained):
        """Test that load_model handles invalid device specification."""
        mock_tokenizer = MagicMock()
        mock_model = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer
        mock_from_pretrained.return_value = mock_model
        
        # Test with invalid device string
        with self.assertRaises(ModelLoadException):
            load_model(self.mock_model_path, device="invalid_device")

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('utils.model_loader.AutoTokenizer.from_pretrained')
    def test_load_model_with_deviation_exception(self, mock_tokenizer, mock_from_pretrained):
        """Test that ModelDeviationException is handled correctly."""
        mock_tokenizer.return_value = self.mock_tokenizer
        mock_from_pretrained.side_effect = ModelDeviationException("Model deviation detected")
        
        with self.assertRaises(ModelDeviationException):
            load_model(self.mock_model_path, device="cpu")


class TestQuantizationConfig(unittest.TestCase):
    """Tests for quantization configuration utilities."""

    def test_get_quantization_config_4bit(self):
        """Test 4-bit quantization config generation."""
        config = get_quantization_config(4)
        self.assertIsNotNone(config)
        self.assertTrue(hasattr(config, 'bnb_4bit_quant_type'))
        self.assertTrue(hasattr(config, 'bnb_4bit_compute_dtype'))

    def test_get_quantization_config_invalid_bits(self):
        """Test that invalid bit quantization raises error."""
        with self.assertRaises(ModelLoadException):
            get_quantization_config(8)  # Only 4-bit is supported


if __name__ == '__main__':
    unittest.main()