"""
Unit tests for utils.metrics.calculate_flops
"""
import unittest
import torch
import torch.nn as nn
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.metrics import calculate_flops


class TestFLOPCounting(unittest.TestCase):

    def test_linear_layer_flops(self):
        """
        Test FLOP calculation for a simple Linear layer.
        Theoretical FLOPs for Linear(in, out) with input (batch, seq, in):
        FLOPs = 2 * batch * seq * in * out
        """
        batch_size = 2
        seq_len = 4
        in_features = 8
        out_features = 16

        model = nn.Linear(in_features, out_features)
        input_shape = (batch_size, seq_len, in_features)

        flops = calculate_flops(model, input_shape)

        # Expected: 2 * 2 * 4 * 8 * 16 = 2048
        expected_flops = 2 * batch_size * seq_len * in_features * out_features

        self.assertEqual(flops, expected_flops)
        self.assertIsInstance(flops, int)

    def test_sequential_model_flops(self):
        """
        Test FLOP calculation for a Sequential model with multiple layers.
        """
        # Model: Linear(10, 20) -> ReLU -> Linear(20, 5)
        # Input: (batch=1, seq=10, in=10)
        
        batch_size = 1
        seq_len = 10
        
        layer1 = nn.Linear(10, 20)
        layer2 = nn.Linear(20, 5)
        model = nn.Sequential(layer1, nn.ReLU(), layer2)
        
        input_shape = (batch_size, seq_len, 10)
        
        flops = calculate_flops(model, input_shape)
        
        # Layer 1: 2 * 1 * 10 * 10 * 20 = 4000
        # Layer 2: 2 * 1 * 10 * 20 * 5 = 2000
        # Total: 6000
        expected_flops = (2 * batch_size * seq_len * 10 * 20) + (2 * batch_size * seq_len * 20 * 5)
        
        self.assertEqual(flops, expected_flops)

    def test_conv1d_flops(self):
        """
        Test FLOP calculation for a Conv1d layer.
        """
        batch_size = 2
        seq_len = 10
        in_channels = 3
        out_channels = 6
        kernel_size = 3
        
        model = nn.Conv1d(in_channels, out_channels, kernel_size)
        # Input for Conv1d is (batch, channels, length)
        # But our function expects input_shape to be passed as (batch, seq, ...) or similar?
        # The function calculates based on dummy_input shape.
        # For Conv1d, the input is (N, C, L).
        # Our calculate_flops creates dummy_input = torch.randn(1, *input_shape).
        # So if input_shape is (C, L), dummy is (1, C, L).
        # But Conv1d expects (N, C, L).
        # Let's adjust the test to match the expected input shape for the model.
        # The function signature is calculate_flops(model, input_shape).
        # It creates dummy_input = torch.randn(1, *input_shape).
        # So if we pass (3, 10), dummy is (1, 3, 10).
        # Conv1d expects (N, C, L). So (1, 3, 10) is valid if N=1, C=3, L=10.
        
        input_shape = (in_channels, seq_len)
        flops = calculate_flops(model, input_shape)
        
        # Conv1d FLOPs: 2 * N * L_out * C_in * C_out * K
        # L_out = (L_in - K + 1) = 10 - 3 + 1 = 8
        # N = 1
        # FLOPs = 2 * 1 * 8 * 3 * 6 * 3 = 864
        
        l_out = seq_len - kernel_size + 1
        expected_flops = 2 * 1 * l_out * in_channels * out_channels * kernel_size
        
        self.assertEqual(flops, expected_flops)

    def test_invalid_input_shape(self):
        """
        Test that invalid input shapes raise errors.
        """
        model = nn.Linear(10, 10)
        
        with self.assertRaises(ValueError):
            calculate_flops(model, ())
        
        with self.assertRaises(ValueError):
            calculate_flops(model, [])

    def test_invalid_model_type(self):
        """
        Test that non-Module models raise errors.
        """
        with self.assertRaises(TypeError):
            calculate_flops("not_a_model", (2, 3))


if __name__ == '__main__':
    unittest.main()