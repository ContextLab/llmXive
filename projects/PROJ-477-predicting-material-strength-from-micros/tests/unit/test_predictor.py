"""
Unit tests for Monte Carlo Dropout confidence interval calculation.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.predictor import (
    enable_dropout,
    disable_dropout,
    verify_coverage,
    run_monte_carlo_dropout
)
from models.cnn import MaterialStrengthCNN
import torch
import torch.nn as nn

class TestDropoutControl(unittest.TestCase):
    """Tests for enabling/disabling dropout layers."""

    def setUp(self):
        self.model = MaterialStrengthCNN()

    def test_enable_dropout_sets_train_mode(self):
        """Test that enable_dropout sets dropout layers to train mode."""
        # Initially dropout should be eval mode (default for loaded models)
        for module in self.model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d)):
                module.eval()
        
        enable_dropout(self.model)
        
        for module in self.model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d)):
                self.assertTrue(module.training)

    def test_disable_dropout_sets_eval_mode(self):
        """Test that disable_dropout sets dropout layers to eval mode."""
        for module in self.model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d)):
                module.train()
        
        disable_dropout(self.model)
        
        for module in self.model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d)):
                self.assertFalse(module.training)

class TestCoverageVerification(unittest.TestCase):
    """Tests for coverage verification logic."""

    def test_perfect_coverage(self):
        """Test with perfect coverage."""
        predictions = np.array([10.0, 20.0, 30.0])
        ci_lower = np.array([5.0, 15.0, 25.0])
        ci_upper = np.array([15.0, 25.0, 35.0])
        true_values = np.array([10.0, 20.0, 30.0])

        stats = verify_coverage(predictions, ci_lower, ci_upper, true_values)

        self.assertEqual(stats["actual_coverage"], 1.0)
        self.assertEqual(stats["status"], "PASS")
        self.assertEqual(stats["samples_in_interval"], 3)

    def test_partial_coverage(self):
        """Test with partial coverage."""
        predictions = np.array([10.0, 20.0, 30.0])
        ci_lower = np.array([5.0, 15.0, 25.0])
        ci_upper = np.array([15.0, 25.0, 35.0])
        true_values = np.array([10.0, 100.0, 30.0])  # Second one is outside

        stats = verify_coverage(predictions, ci_lower, ci_upper, true_values)

        self.assertEqual(stats["actual_coverage"], 2/3)
        self.assertEqual(stats["samples_in_interval"], 2)

    def test_no_coverage(self):
        """Test with no coverage."""
        predictions = np.array([10.0, 20.0, 30.0])
        ci_lower = np.array([5.0, 15.0, 25.0])
        ci_upper = np.array([15.0, 25.0, 35.0])
        true_values = np.array([100.0, 200.0, 300.0])

        stats = verify_coverage(predictions, ci_lower, ci_upper, true_values)

        self.assertEqual(stats["actual_coverage"], 0.0)
        self.assertEqual(stats["status"], "WARN")
        self.assertEqual(stats["samples_in_interval"], 0)

class TestMonteCarloDropoutIntegration(unittest.TestCase):
    """Integration tests for MC Dropout with a mock dataset."""

    @patch('eval.predictor.DataLoader')
    def test_mc_dropout_returns_correct_shapes(self, mock_dataloader):
        """Test that MC Dropout returns arrays of correct shape."""
        # Create a simple model
        model = MaterialStrengthCNN()
        model.eval()
        
        # Mock dataset
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=4)
        
        # Mock batch
        mock_images = torch.randn(4, 3, 224, 224)
        mock_dataloader.return_value.__iter__ = MagicMock(return_value=iter([{"image": mock_images}]))
        
        # Run MC Dropout
        mean_preds, ci_lower, ci_upper = run_monte_carlo_dropout(
            model, mock_dataset, n_samples=10, batch_size=4, device="cpu"
        )
        
        # Check shapes
        self.assertEqual(mean_preds.shape, (4,))
        self.assertEqual(ci_lower.shape, (4,))
        self.assertEqual(ci_upper.shape, (4,))
        
        # Check that ci_lower < mean < ci_upper
        self.assertTrue(np.all(ci_lower <= mean_preds))
        self.assertTrue(np.all(mean_preds <= ci_upper))

if __name__ == "__main__":
    unittest.main()