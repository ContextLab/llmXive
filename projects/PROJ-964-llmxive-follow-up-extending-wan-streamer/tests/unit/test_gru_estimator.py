"""
Unit tests for the GRU Estimator model.
"""

import pytest
import torch
import os
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.gru_estimator import GRUEstimator, compute_uncertainty_correlation, save_checkpoint, load_checkpoint


class TestGRUEstimatorArchitecture:
    """Tests for the GRU architecture and forward pass."""

    def test_model_initialization(self):
        """Test that the model initializes correctly."""
        model = GRUEstimator(input_dim=128, hidden_dim=64, num_layers=2)
        assert model.input_dim == 128
        assert model.hidden_dim == 64
        assert model.num_layers == 2
        assert model.gru is not None
        assert model.fc is not None

    def test_forward_pass_shape(self):
        """Test that forward pass returns correct shape."""
        model = GRUEstimator(input_dim=128, hidden_dim=64, num_layers=2)
        batch_size = 32
        seq_len = 10
        x = torch.randn(batch_size, seq_len, 128)
        
        output = model(x)
        
        assert output.shape == (batch_size, 2), f"Expected (32, 2), got {output.shape}"

    def test_output_ranges(self):
        """Test that outputs are within expected ranges."""
        model = GRUEstimator(input_dim=128, hidden_dim=64, num_layers=2)
        x = torch.randn(10, 5, 128)
        
        with torch.no_grad():
            output = model(x)
        
        delta_magnitude = output[:, 0]
        uncertainty = output[:, 1]
        
        # Delta magnitude should be non-negative (softplus)
        assert torch.all(delta_magnitude >= 0), "Delta magnitude should be >= 0"
        
        # Uncertainty should be in [0, 1] (sigmoid)
        assert torch.all(uncertainty >= 0.0) and torch.all(uncertainty <= 1.0), "Uncertainty should be in [0, 1]"


class TestUncertaintyCorrelation:
    """Tests for the uncertainty correlation metric."""

    def test_perfect_correlation(self):
        """Test correlation calculation with perfectly correlated data."""
        # Create data where uncertainty perfectly predicts error
        n = 100
        pred_uncertainty = torch.linspace(0, 1, n)
        actual_error = pred_uncertainty * 2.0  # Perfect linear relationship
        
        pred_delta = torch.zeros(n)
        true_delta = torch.zeros(n)
        
        # We need to construct the tensors as expected by the function
        predictions = torch.stack([pred_delta, pred_uncertainty], dim=1)
        targets = torch.stack([true_delta, torch.zeros(n)], dim=1) # Target uncertainty not used in calc
        
        # Actually, the function uses:
        # actual_error = |pred_delta - true_delta|
        # We need to set pred_delta and true_delta such that error correlates with pred_uncertainty
        
        # Let's make pred_delta vary and true_delta = 0, so error = |pred_delta|
        # And make pred_uncertainty correlate with |pred_delta|
        true_delta = torch.zeros(n)
        pred_delta = pred_uncertainty * 2.0  # error = 2 * uncertainty
        
        predictions = torch.stack([pred_delta, pred_uncertainty], dim=1)
        targets = torch.stack([true_delta, torch.zeros(n)], dim=1)
        
        r = compute_uncertainty_correlation(predictions, targets)
        
        # Should be close to 1.0
        assert abs(r - 1.0) < 0.01, f"Expected r ~ 1.0, got {r}"

    def test_no_correlation(self):
        """Test correlation with uncorrelated data."""
        n = 100
        pred_uncertainty = torch.rand(n)
        pred_delta = torch.rand(n)
        true_delta = torch.rand(n)
        
        predictions = torch.stack([pred_delta, pred_uncertainty], dim=1)
        targets = torch.stack([true_delta, torch.zeros(n)], dim=1)
        
        r = compute_uncertainty_correlation(predictions, targets)
        
        # Should be close to 0 (or at least not 1.0)
        # With random data, it's unlikely to be exactly 0, but should be low
        assert abs(r) < 0.5, f"Expected low correlation, got {r}"


class TestCheckpointing:
    """Tests for model checkpointing."""

    def test_save_and_load_checkpoint(self, tmp_path):
        """Test saving and loading a checkpoint."""
        model = GRUEstimator(input_dim=128, hidden_dim=64, num_layers=2)
        checkpoint_path = tmp_path / "test_checkpoint.pt"
        
        save_checkpoint(model, None, epoch=0, path=str(checkpoint_path), correlation_score=0.85)
        
        assert checkpoint_path.exists(), "Checkpoint file was not created"
        
        loaded_model, metadata = load_checkpoint(str(checkpoint_path), torch.device("cpu"))
        
        assert loaded_model is not None
        assert metadata['epoch'] == 0
        assert metadata['correlation_score'] == 0.85
        
        # Check model weights are loaded
        for p1, p2 in zip(model.parameters(), loaded_model.parameters()):
            assert torch.equal(p1, p2), "Model weights do not match after loading"

    def test_save_checkpoint_creates_directory(self, tmp_path):
        """Test that save_checkpoint creates the directory if it doesn't exist."""
        model = GRUEstimator(input_dim=128, hidden_dim=64, num_layers=2)
        nested_path = tmp_path / "subdir" / "checkpoint.pt"
        
        save_checkpoint(model, None, epoch=0, path=str(nested_path), correlation_score=0.85)
        
        assert nested_path.exists(), "Checkpoint file was not created in nested directory"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])