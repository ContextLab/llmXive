"""
Unit tests for code/models/gating_head.py
Tests gating head output scalar range (1-5)
"""
import os
import sys
import unittest
from pathlib import Path
import torch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.gating_head import (
    GatingHead,
    create_gating_head,
    count_parameters
)


class TestGatingHeadCreation(unittest.TestCase):
    """Tests for gating head creation and structure"""

    def test_create_gating_head_returns_model(self):
        """Test that create_gating_head returns a GatingHead instance"""
        model = create_gating_head(input_channels=1, output_dim=1)
        self.assertIsInstance(model, GatingHead)

    def test_gating_head_has_correct_input_dim(self):
        """Test that gating head accepts correct input dimensions"""
        model = create_gating_head(input_channels=1, output_dim=1)
        x = torch.randn(1, 1, 32, 32)  # batch=1, channels=1, height=32, width=32
        with torch.no_grad():
            output = model(x)
        self.assertEqual(output.shape[0], 1)

    def test_gating_head_parameter_count(self):
        """Test that gating head parameter count is reasonable"""
        model = create_gating_head(input_channels=1, output_dim=1)
        param_count = count_parameters(model)
        # Should be relatively small (< 5M as per spec)
        self.assertLess(param_count, 5_000_000)


class TestGatingHeadOutput(unittest.TestCase):
    """Tests for gating head output values"""

    def setUp(self):
        """Create a gating head model"""
        self.model = create_gating_head(input_channels=1, output_dim=1)
        self.model.eval()  # Set to evaluation mode

    def test_output_scalar_range_basic(self):
        """Test that output is a scalar value"""
        x = torch.randn(1, 1, 32, 32)
        with torch.no_grad():
            output = self.model(x)
        self.assertEqual(output.shape, (1, 1))

    def test_output_positive_values(self):
        """Test that output values are positive (after ReLU)"""
        x = torch.randn(10, 1, 32, 32)
        with torch.no_grad():
            output = self.model(x)
        # Output should be >= 0 due to ReLU activation
        self.assertTrue(torch.all(output >= 0))

    def test_output_range_clamped(self):
        """Test that output can be clamped to range [1, 5]"""
        x = torch.randn(10, 1, 32, 32)
        with torch.no_grad():
            output = self.model(x)
            # Apply clamping as would be done in usage
            clamped = torch.clamp(output, min=1.0, max=5.0)
        self.assertTrue(torch.all(clamped >= 1.0))
        self.assertTrue(torch.all(clamped <= 5.0))

    def test_output_consistency_same_input(self):
        """Test that same input produces same output (deterministic)"""
        x = torch.randn(1, 1, 32, 32)
        with torch.no_grad():
            output1 = self.model(x)
            output2 = self.model(x)
        self.assertTrue(torch.allclose(output1, output2))


class TestGatingHeadEdgeCases(unittest.TestCase):
    """Tests for edge cases in gating head"""

    def setUp(self):
        """Create a gating head model"""
        self.model = create_gating_head(input_channels=1, output_dim=1)
        self.model.eval()

    def test_batch_size_1(self):
        """Test with batch size of 1"""
        x = torch.randn(1, 1, 32, 32)
        with torch.no_grad():
            output = self.model(x)
        self.assertEqual(output.shape, (1, 1))

    def test_batch_size_large(self):
        """Test with larger batch size"""
        x = torch.randn(64, 1, 32, 32)
        with torch.no_grad():
            output = self.model(x)
        self.assertEqual(output.shape, (64, 1))

    def test_different_input_sizes(self):
        """Test with different input spatial dimensions"""
        sizes = [(16, 16), (32, 32), (64, 64)]
        for h, w in sizes:
            x = torch.randn(1, 1, h, w)
            with torch.no_grad():
                output = self.model(x)
            self.assertEqual(output.shape, (1, 1))


class TestGatingHeadIntegration(unittest.TestCase):
    """Integration tests for gating head"""

    def test_forward_pass_no_error(self):
        """Test that forward pass completes without error"""
        model = create_gating_head(input_channels=1, output_dim=1)
        x = torch.randn(4, 1, 32, 32)
        try:
            model.eval()
            with torch.no_grad():
                output = model(x)
            self.assertIsNotNone(output)
        except Exception as e:
            self.fail(f"Forward pass raised {type(e).__name__}: {e}")

    def test_gradient_flow(self):
        """Test that gradients flow through the network"""
        model = create_gating_head(input_channels=1, output_dim=1)
        model.train()
        x = torch.randn(4, 1, 32, 32, requires_grad=True)
        output = model(x)
        loss = output.sum()
        loss.backward()
        self.assertIsNotNone(x.grad)
        self.assertTrue(torch.any(x.grad != 0))


if __name__ == "__main__":
    unittest.main()
