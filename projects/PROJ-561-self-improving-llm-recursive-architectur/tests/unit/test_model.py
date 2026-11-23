"""
Unit tests for pipeline/model.py
Specifically tests the GPU-disabled loader for GPT-2 124M (Task T006).
"""
import unittest
import sys
import os
import torch
from unittest.mock import patch, MagicMock, PropertyMock

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.model import load_gpt2_124m_cpu_only, get_model_param_count, validate_modification_distinctness

class TestModelLoaderT006(unittest.TestCase):
    """Tests for the GPU-disabled GPT-2 loader."""

    @patch('pipeline.model.GPT2LMHeadModel')
    @patch('pipeline.model.GPT2Config')
    def test_load_gpt2_cpu_only_forces_cpu(self, mock_config, mock_model_class):
        """
        Verify that the loader forces the model to CPU even if CUDA is available.
        """
        # Mock the config and model
        mock_config_instance = MagicMock()
        mock_config_instance.from_pretrained.return_value = mock_config_instance
        
        mock_model_instance = MagicMock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.eval.return_value = mock_model_instance
        mock_model_class.from_pretrained.return_value = mock_model_instance

        # Patch torch.device to ensure we know what's being called
        with patch('pipeline.model.torch.device') as mock_device:
            mock_device_instance = MagicMock()
            mock_device.return_value = mock_device_instance
            
            # Call the loader
            model, config = load_gpt2_124m_cpu_only(checkpoint_path=None, force_cpu=True)

            # Assertions
            # 1. Verify torch.device("cpu") was called
            mock_device.assert_called_with("cpu")
            
            # 2. Verify model.to() was called with the CPU device
            mock_model_instance.to.assert_called_with(mock_device_instance)
            
            # 3. Verify eval() was called
            mock_model_instance.eval.assert_called_once()

    @patch('pipeline.model.GPT2LMHeadModel')
    @patch('pipeline.model.GPT2Config')
    def test_load_gpt2_handles_missing_dependency(self, mock_config, mock_model_class):
        """
        Verify that an error is raised if transformers is not available.
        """
        # Simulate ImportError during import
        with patch('builtins.__import__', side_effect=ImportError("No module named 'transformers'")):
            with self.assertRaises(RuntimeError) as context:
                load_gpt2_124m_cpu_only(checkpoint_path=None)
            
            self.assertIn("transformers", str(context.exception))

    def test_get_model_param_count(self):
        """
        Verify parameter counting works correctly on a simple model.
        """
        class SimpleModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = torch.nn.Linear(10, 20)
        
        model = SimpleModel()
        count = get_model_param_count(model)
        
        # Linear(10, 20) has 10*20 weights + 20 biases = 220 params
        self.assertEqual(count, 220)

    def test_validate_modification_distinctness_empty_history(self):
        """
        Verify that a proposal is valid if history is empty.
        """
        proposal = {'num_layers': 12, 'hidden_size': 768}
        self.assertTrue(validate_modification_distinctness(proposal, []))

    def test_validate_modification_distinctness_hamming(self):
        """
        Verify Hamming distance check returns True if different.
        """
        proposal = {'num_layers': 12, 'hidden_size': 768, 'num_heads': 12, 'activation': 'gelu'}
        history = [{'num_layers': 12, 'hidden_size': 768, 'num_heads': 12, 'activation': 'relu'}]
        
        # Activation differs -> Hamming distance >= 1
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_validate_modification_distinctness_same(self):
        """
        Verify that identical proposals return False.
        """
        proposal = {'num_layers': 12, 'hidden_size': 768, 'num_heads': 12, 'activation': 'gelu'}
        history = [{'num_layers': 12, 'hidden_size': 768, 'num_heads': 12, 'activation': 'gelu'}]
        
        # Identical -> Hamming distance 0, param count 0 change
        self.assertFalse(validate_modification_distinctness(proposal, history))

if __name__ == '__main__':
    unittest.main()