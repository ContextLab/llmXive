"""
Unit test for gating head output scalar range (1-5).

This test verifies that the GatingHead module produces scalar outputs
strictly within the range [1.0, 5.0] as specified for the Moebius-Dynamic
architecture.
"""
import os
import sys
import unittest
import torch
import torch.nn as nn
import numpy as np

# Add project root to path to allow imports from code/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from code.models.gating_head import GatingHead
from code.utils.seed import set_seed


class TestGatingHeadRange(unittest.TestCase):
    """Test suite for GatingHead output range constraints."""

    def setUp(self):
        """Set up test fixtures."""
        set_seed(42)
        self.device = torch.device("cpu")
        
        # Initialize GatingHead with standard configuration
        # Input channels: 3 (RGB images)
        # Output: scalar complexity score in range [1, 5]
        self.gating_head = GatingHead(
            in_channels=3,
            hidden_channels=16,
            out_channels=1
        ).to(self.device)
        
        # Create a batch of dummy images (N, C, H, W)
        self.batch_size = 8
        self.image_size = 256
        self.dummy_images = torch.randn(
            self.batch_size, 3, self.image_size, self.image_size,
            device=self.device
        )

    def test_output_shape(self):
        """Verify output shape matches expected scalar per sample."""
        self.gating_head.eval()
        with torch.no_grad():
            outputs = self.gating_head(self.dummy_images)
        
        # Output should be (batch_size, 1) or (batch_size,)
        self.assertEqual(outputs.shape[0], self.batch_size)
        self.assertIn(outputs.ndim, [1, 2])
        if outputs.ndim == 2:
            self.assertEqual(outputs.shape[1], 1)

    def test_output_range_min(self):
        """Verify all outputs are >= 1.0."""
        self.gating_head.eval()
        with torch.no_grad():
            outputs = self.gating_head(self.dummy_images)
        
        # Flatten to 1D for easy checking
        flat_outputs = outputs.view(-1)
        
        min_val = flat_outputs.min().item()
        self.assertGreaterEqual(min_val, 1.0, 
            f"Output min {min_val} is below lower bound 1.0")

    def test_output_range_max(self):
        """Verify all outputs are <= 5.0."""
        self.gating_head.eval()
        with torch.no_grad():
            outputs = self.gating_head(self.dummy_images)
        
        flat_outputs = outputs.view(-1)
        
        max_val = flat_outputs.max().item()
        self.assertLessEqual(max_val, 5.0,
            f"Output max {max_val} is above upper bound 5.0")

    def test_output_range_comprehensive(self):
        """Comprehensive test: all outputs strictly within [1.0, 5.0]."""
        self.gating_head.eval()
        
        # Test with multiple random seeds and batches
        for seed in [42, 123, 456, 789, 101112]:
            set_seed(seed)
            batch_images = torch.randn(
                self.batch_size, 3, self.image_size, self.image_size,
                device=self.device
            )
            
            with torch.no_grad():
                outputs = self.gating_head(batch_images)
            
            flat_outputs = outputs.view(-1)
            min_val = flat_outputs.min().item()
            max_val = flat_outputs.max().item()
            
            self.assertGreaterEqual(min_val, 1.0,
                f"Seed {seed}: Output min {min_val} < 1.0")
            self.assertLessEqual(max_val, 5.0,
                f"Seed {seed}: Output max {max_val} > 5.0")

    def test_gradient_flow(self):
        """Verify gradients flow through the gating head."""
        self.gating_head.train()
        batch_images = self.dummy_images.clone().requires_grad_(True)
        
        outputs = self.gating_head(batch_images)
        loss = outputs.sum()
        loss.backward()
        
        self.assertIsNotNone(batch_images.grad)
        self.assertTrue(batch_images.grad.abs().sum().item() > 0,
            "Gradients should flow through the gating head")

    def test_parameter_count(self):
        """Verify the gating head stays within the 5M parameter budget."""
        total_params = sum(p.numel() for p in self.gating_head.parameters())
        self.assertLessEqual(total_params, 5_000_000,
            f"Gating head has {total_params} params, exceeds 5M budget")


def run_tests():
    """Run all tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGatingHeadRange)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    run_tests()