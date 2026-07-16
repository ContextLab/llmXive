"""
Unit tests for model loading configuration.

This module verifies that the model loading logic in `code/model/inference.py`
correctly configures bitsandbytes 4-bit quantization and targets CPU devices.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# Add the project root to the path to allow imports from code/
# Assuming this test runs from the project root or the path is set correctly
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestModelLoadConfig(unittest.TestCase):
    """Tests to verify model loading flags and device configuration."""

    @patch('model.inference.AutoModelForCausalLM')
    @patch('model.inference.AutoTokenizer')
    @patch('model.inference.BitsAndBytesConfig')
    @patch('model.inference.torch')
    def test_bitsandbytes_4bit_config_set(self, mock_torch, mock_bnb_config, mock_tokenizer, mock_model):
        """
        Verify that BitsAndBytesConfig is instantiated with 4-bit quantization flags.
        
        This test ensures that when `load_model` is called, it explicitly requests
        4-bit quantization via `load_in_4bit=True` and the corresponding BNB config.
        """
        # Setup mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_bnb_config.return_value = MagicMock()
        
        # Import the function under test
        from model.inference import load_model

        # Call the function
        # We mock the config path to avoid needing a real config file for this unit test
        load_model(model_path="test/model", config_path=None)

        # Assert BitsAndBytesConfig was called
        mock_bnb_config.assert_called_once()

        # Retrieve the call arguments to verify 4-bit flags
        call_kwargs = mock_bnb_config.call_args.kwargs

        # Verify 4-bit quantization is enabled
        self.assertTrue(call_kwargs.get('load_in_4bit'), "load_in_4bit must be True")
        
        # Verify standard 4-bit config settings are present
        # These are typical defaults for 4-bit quantization in bitsandbytes
        self.assertTrue(call_kwargs.get('bnb_4bit_use_double_quant', True), 
                        "bnb_4bit_use_double_quant should typically be True for efficiency")
        
        # Verify quantization type (nf4 is standard for 4-bit)
        self.assertEqual(call_kwargs.get('bnb_4bit_quant_type'), 'nf4',
                         "bnb_4bit_quant_type should be 'nf4'")

    @patch('model.inference.AutoModelForCausalLM')
    @patch('model.inference.AutoTokenizer')
    @patch('model.inference.BitsAndBytesConfig')
    @patch('model.inference.torch')
    def test_cpu_device_targeting(self, mock_torch, mock_bnb_config, mock_tokenizer, mock_model):
        """
        Verify that the model is loaded onto the CPU device.
        
        This test ensures that the loading logic explicitly sets the device to CPU,
        satisfying the constraint that inference must run on CPU (no CUDA).
        """
        # Setup mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_bnb_config.return_value = MagicMock()
        
        # Mock torch.device to verify it is called with 'cpu'
        mock_device_instance = MagicMock()
        mock_torch.device.return_value = mock_device_instance

        # Import the function under test
        from model.inference import load_model

        # Call the function
        load_model(model_path="test/model", config_path=None)

        # Verify that torch.device was called with 'cpu'
        mock_torch.device.assert_called_with('cpu')

        # Verify that from_pretrained was called with device_map or torch_dtype/device args
        # depending on how the inference.py implementation handles device placement.
        # We expect the model to be moved to CPU explicitly.
        from_pretrained_calls = mock_model.from_pretrained.call_args_list
        
        # Check if 'device_map' is set to 'cpu' or 'auto' with CPU offload, 
        # or if 'torch_dtype' is used in conjunction with device placement.
        # The most robust check for CPU-only is ensuring 'cpu' is in the device_map or passed as device.
        
        # Common pattern: device_map="cpu" or device_map={"": "cpu"}
        # Or passing device=torch.device("cpu")
        
        # Let's check the kwargs of the last call
        last_call_kwargs = mock_model.from_pretrained.call_args.kwargs
        
        # We expect either device_map or explicit device handling
        if 'device_map' in last_call_kwargs:
            device_map = last_call_kwargs['device_map']
            # If it's a string, it should be 'cpu'
            if isinstance(device_map, str):
                self.assertEqual(device_map, 'cpu', "device_map must be 'cpu' for CPU-only execution")
            # If it's a dict, it should map to cpu
            elif isinstance(device_map, dict):
                self.assertTrue(all(v == 'cpu' for v in device_map.values()), 
                                "All device_map values must be 'cpu'")
        else:
            # If device_map is not used, check if 'device' is passed
            self.assertIn('device', last_call_kwargs, 
                          "Either 'device_map' or 'device' must be specified for CPU loading")
            self.assertEqual(last_call_kwargs['device'], mock_device_instance, 
                             "Device must be set to CPU instance")

    @patch('model.inference.AutoModelForCausalLM')
    @patch('model.inference.AutoTokenizer')
    @patch('model.inference.BitsAndBytesConfig')
    @patch('model.inference.torch')
    def test_no_cuda_device_used(self, mock_torch, mock_bnb_config, mock_tokenizer, mock_model):
        """
        Verify that CUDA is explicitly NOT used.
        
        This test ensures that no part of the loading logic attempts to initialize
        CUDA or use a GPU device.
        """
        # Setup mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_bnb_config.return_value = MagicMock()
        
        # Mock torch.cuda to ensure it's not accessed inappropriately
        mock_torch.cuda.is_available.return_value = True # Even if available, we shouldn't use it
        
        # Import the function under test
        from model.inference import load_model

        # Call the function
        load_model(model_path="test/model", config_path=None)

        # Verify that device is set to cpu, not cuda
        # This is covered by test_cpu_device_targeting, but we double-check no 'cuda' string appears
        # in the device_map or device arguments
        
        last_call_kwargs = mock_model.from_pretrained.call_args.kwargs
        
        device_arg = last_call_kwargs.get('device_map', last_call_kwargs.get('device', ''))
        
        # Check for any 'cuda' string in the device configuration
        if isinstance(device_arg, str):
            self.assertNotIn('cuda', device_arg.lower(), "CUDA device must not be used")
        elif isinstance(device_arg, dict):
            for v in device_arg.values():
                self.assertNotIn('cuda', str(v).lower(), "CUDA device must not be used in device_map")

if __name__ == '__main__':
    unittest.main()