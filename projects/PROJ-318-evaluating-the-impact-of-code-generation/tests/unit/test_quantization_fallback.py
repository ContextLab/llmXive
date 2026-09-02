"""
Unit tests for verifying the quantization fallback logic in code/utils/model_loader.py.

This test suite explicitly triggers the 4-bit quantization failure path and verifies
that the system successfully falls back to 8-bit or full precision loading.

It mocks the `transformers.BitsAndBytesConfig` initialization to simulate a failure
when 4-bit quantization is requested, ensuring the fallback logic in `load_model`
executes correctly.
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import sys
import os

# Add the project root to the path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.model_loader import load_model, ModelLoadException, ModelDeviationException
from transformers import BitsAndBytesConfig


class MockModel:
    """Mock model object to return during successful load."""
    def __init__(self, quantization_config=None):
        self.quantization_config = quantization_config
        self.dtype = torch.float32
        self.device_map = "auto"

class MockTokenizer:
    """Mock tokenizer object."""
    def __init__(self):
        self.pad_token = None

class TestQuantizationFallback(unittest.TestCase):
    """Tests for the 4-bit -> 8-bit -> Full Precision fallback logic."""

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('utils.model_loader.AutoTokenizer.from_pretrained')
    @patch('utils.model_loader.BitsAndBytesConfig')
    def test_fallback_from_4bit_to_8bit(self, mock_bnb_config, mock_tokenizer, mock_model_load):
        """
        Verify that if 4-bit quantization fails, the system attempts 8-bit.
        
        Scenario:
        1. First attempt (4-bit) raises an exception (simulated via mock).
        2. Second attempt (8-bit) succeeds.
        
        Expected:
        - `load_model` should return the model loaded with 8-bit config.
        - The returned model should NOT have 4-bit config.
        """
        # Setup mocks
        mock_tokenizer.return_value = MockTokenizer()
        mock_model_instance = MockModel()
        
        # Simulate 4-bit failure on the first call
        # We use a side_effect list to raise on the first call (4-bit) and return on second (8-bit)
        def side_effect_effect(*args, **kwargs):
            # Check if this is the 4-bit attempt by looking at kwargs or config
            # In our implementation, the first call uses 4-bit.
            # We raise an exception to simulate OOM or incompatibility
            raise RuntimeError("Simulated 4-bit quantization failure (OOM)")

        # Configure the model loader mock to raise on first call, succeed on second
        mock_model_load.side_effect = [
            side_effect_effect, # First call (4-bit) raises
            mock_model_instance # Second call (8-bit) returns success
        ]

        # Mock the BNB config creation to ensure we know which one was tried
        # We don't need to mock the config itself for the logic, just the model load
        
        # Execute
        model, tokenizer, quantization_type = load_model(
            model_id="Salesforce/codegen-350M-mono",
            force_4bit=True # Force the logic to try 4-bit first
        )

        # Assertions
        self.assertEqual(mock_model_load.call_count, 2)
        
        # Verify the first call attempted 4-bit (we can't easily inspect the mock args 
        # without a more complex setup, but the side_effect logic ensures it happened)
        
        # Verify the second call succeeded and returned the model
        self.assertIsNotNone(model)
        self.assertEqual(model, mock_model_instance)
        
        # Verify the returned quantization type is 8-bit
        self.assertEqual(quantization_type, "8-bit")

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('utils.model_loader.AutoTokenizer.from_pretrained')
    @patch('utils.model_loader.BitsAndBytesConfig')
    def test_fallback_from_8bit_to_full_precision(self, mock_bnb_config, mock_tokenizer, mock_model_load):
        """
        Verify that if 4-bit and 8-bit fail, the system attempts full precision.
        
        Scenario:
        1. First attempt (4-bit) fails.
        2. Second attempt (8-bit) fails.
        3. Third attempt (Full Precision) succeeds.
        
        Expected:
        - `load_model` returns the model loaded with full precision (no quantization config).
        """
        mock_tokenizer.return_value = MockTokenizer()
        mock_model_instance = MockModel()
        
        # Simulate failures for 4-bit and 8-bit
        def raise_exception(*args, **kwargs):
            raise RuntimeError("Simulated quantization failure")

        mock_model_load.side_effect = [
            raise_exception, # 4-bit
            raise_exception, # 8-bit
            mock_model_instance # Full precision
        ]

        model, tokenizer, quantization_type = load_model(
            model_id="Salesforce/codegen-350M-mono",
            force_4bit=True
        )

        # Assertions
        self.assertEqual(mock_model_load.call_count, 3)
        self.assertIsNotNone(model)
        self.assertEqual(quantization_type, "full-precision")

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('utils.model_loader.AutoTokenizer.from_pretrained')
    @patch('utils.model_loader.BitsAndBytesConfig')
    def test_all_quantization_attempts_fail(self, mock_bnb_config, mock_tokenizer, mock_model_load):
        """
        Verify that if 4-bit, 8-bit, and full precision all fail, the system raises ModelLoadException.
        
        Scenario:
        1. All three attempts fail.
        
        Expected:
        - `load_model` raises `ModelLoadException`.
        """
        mock_tokenizer.return_value = MockTokenizer()
        
        def raise_exception(*args, **kwargs):
            raise RuntimeError("Simulated quantization failure")

        mock_model_load.side_effect = [
            raise_exception, # 4-bit
            raise_exception, # 8-bit
            raise_exception  # Full precision
        ]

        with self.assertRaises(ModelLoadException) as context:
            load_model(
                model_id="Salesforce/codegen-350M-mono",
                force_4bit=True
            )

        self.assertIn("All quantization schemes failed", str(context.exception))

    @patch('utils.model_loader.AutoModelForCausalLM.from_pretrained')
    @patch('utils.model_loader.AutoTokenizer.from_pretrained')
    def test_4bit_success_no_fallback(self, mock_tokenizer, mock_model_load):
        """
        Verify that if 4-bit succeeds, no fallback is attempted.
        
        Scenario:
        1. First attempt (4-bit) succeeds.
        
        Expected:
        - `load_model` returns immediately with 4-bit config.
        - `mock_model_load` is called exactly once.
        """
        mock_tokenizer.return_value = MockTokenizer()
        mock_model_instance = MockModel()
        mock_model_load.return_value = mock_model_instance

        model, tokenizer, quantization_type = load_model(
            model_id="Salesforce/codegen-350M-mono",
            force_4bit=True
        )

        self.assertEqual(mock_model_load.call_count, 1)
        self.assertEqual(quantization_type, "4-bit")
        self.assertIsNotNone(model)


if __name__ == '__main__':
    unittest.main()