"""
Unit tests for the evaluation module (T019).
"""
import pytest
import numpy as np
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from src.analysis.evaluate import calculate_and_save_metrics, run_inference


class TestCalculateAndSaveMetrics:
    """Tests for the metrics calculation and saving logic."""

    def test_calculate_and_save_metrics_basic(self):
        """Test basic metric calculation and file creation."""
        predictions = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        targets = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            metrics = calculate_and_save_metrics(predictions, targets, output_path)
            
            # Check file exists
            assert os.path.exists(output_path)
            
            # Check metrics content
            assert "mae" in metrics
            assert "rmse" in metrics
            assert "r2" in metrics
            
            # Check values are finite
            assert np.isfinite(metrics["mae"])
            assert np.isfinite(metrics["rmse"])
            assert np.isfinite(metrics["r2"])

    def test_calculate_and_save_metrics_empty_input(self):
        """Test that empty input raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            with pytest.raises(ValueError):
                calculate_and_save_metrics(np.array([]), np.array([]), output_path)

    def test_calculate_and_save_metrics_mismatched_lengths(self):
        """Test that mismatched lengths raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            with pytest.raises(ValueError):
                calculate_and_save_metrics(
                    np.array([1.0, 2.0]),
                    np.array([1.0, 2.0, 3.0]),
                    output_path
                )

    def test_calculate_and_save_metrics_perfect_prediction(self):
        """Test R2 = 1.0 for perfect predictions."""
        predictions = np.array([1.0, 2.0, 3.0])
        targets = np.array([1.0, 2.0, 3.0])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            metrics = calculate_and_save_metrics(predictions, targets, output_path)
            
            # Allow for small floating point errors
            assert np.isclose(metrics["r2"], 1.0, atol=1e-5)

    def test_calculate_and_save_metrics_output_format(self):
        """Test that the output JSON is valid and contains expected keys."""
        predictions = np.array([1.0, 2.0])
        targets = np.array([1.5, 2.5])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "metrics.json")
            calculate_and_save_metrics(predictions, targets, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, dict)
            assert "mae" in data
            assert "rmse" in data
            assert "r2" in data
            assert isinstance(data["mae"], float)
            assert isinstance(data["rmse"], float)
            assert isinstance(data["r2"], float)


class TestRunInference:
    """Tests for the inference logic (mocked model)."""

    def test_run_inference_mocked_model(self):
        """Test inference with a mocked model and data loader."""
        # Create a mock model
        mock_model = MagicMock()
        mock_model.eval = MagicMock()
        mock_model.to = MagicMock(return_value=mock_model)
        
        # Mock the forward pass to return specific values
        # We need to simulate the batch iteration
        def mock_forward(x, edge_index, batch=None):
            # Return a tensor of ones with the same shape as x.sum(dim=0) if batched, else just ones
            # Simplified: return a tensor of shape [batch_size] with value 0.5
            batch_size = x.shape[0] if x.dim() > 0 else 1
            return torch.full((batch_size,), 0.5)
        
        mock_model.__call__ = mock_forward
        
        # Create a mock DataLoader
        # We need to create a mock batch that yields x, edge_index, batch_idx, y
        mock_batch = MagicMock()
        mock_batch.x = torch.tensor([[1.0], [2.0]])
        mock_batch.edge_index = torch.tensor([[0], [1]])
        mock_batch.batch = torch.tensor([0, 1])
        mock_batch.y = torch.tensor([[0.4], [0.6]])
        
        mock_loader = MagicMock()
        mock_loader.__iter__ = MagicMock(return_value=iter([mock_batch]))
        
        preds, trues = run_inference(mock_model, mock_loader, device="cpu")
        
        assert len(preds) == 2
        assert len(trues) == 2
        assert np.allclose(preds, [0.5, 0.5])
        assert np.allclose(trues, [0.4, 0.6])

# Import torch for the mock test
import torch