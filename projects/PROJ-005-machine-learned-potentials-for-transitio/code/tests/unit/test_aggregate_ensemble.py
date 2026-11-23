"""
Unit tests for the ensemble aggregation logic.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import numpy as np
import pytest

from src.models.aggregate_ensemble import (
    load_model_checkpoints,
    aggregate_predictions,
    compute_ensemble_variance_metrics,
    run_aggregation
)


class TestAggregatePredictions:
    """Tests for aggregate_predictions function."""

    def test_aggregate_single_model(self):
        """Test aggregation with a single model."""
        predictions = [np.array([1.0, 2.0, 3.0])]
        result = aggregate_predictions(predictions)
        
        assert np.allclose(result['mean'], [1.0, 2.0, 3.0])
        assert np.allclose(result['variance'], [0.0, 0.0, 0.0])
        assert np.allclose(result['std'], [0.0, 0.0, 0.0])

    def test_aggregate_multiple_models(self):
        """Test aggregation with multiple models."""
        predictions = [
            np.array([1.0, 2.0, 3.0]),
            np.array([1.1, 2.1, 3.1]),
            np.array([0.9, 1.9, 2.9])
        ]
        result = aggregate_predictions(predictions)
        
        assert np.allclose(result['mean'], [1.0, 2.0, 3.0])
        # Variance should be non-zero
        assert np.all(result['variance'] > 0)
        assert np.allclose(result['std'], np.sqrt(result['variance']))

    def test_aggregate_empty_list(self):
        """Test that aggregation fails with empty list."""
        with pytest.raises(ValueError):
            aggregate_predictions([])


class TestComputeVarianceMetrics:
    """Tests for compute_ensemble_variance_metrics function."""

    def test_variance_metrics_computation(self):
        """Test variance metrics computation."""
        variance_array = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        metrics = compute_ensemble_variance_metrics(variance_array)
        
        assert abs(metrics['mean_variance'] - 0.3) < 1e-6
        assert metrics['min_variance'] == 0.1
        assert metrics['max_variance'] == 0.5
        assert 'std_variance' in metrics

    def test_variance_metrics_all_same(self):
        """Test variance metrics with constant variance."""
        variance_array = np.array([0.5, 0.5, 0.5, 0.5])
        metrics = compute_ensemble_variance_metrics(variance_array)
        
        assert abs(metrics['mean_variance'] - 0.5) < 1e-6
        assert metrics['std_variance'] < 1e-6  # Should be very small


class TestLoadModelCheckpoints:
    """Tests for load_model_checkpoints function."""

    def test_load_checkpoints(self, tmp_path):
        """Test loading multiple checkpoints."""
        # Create mock checkpoint files
        seeds = [1, 2, 3]
        for seed in seeds:
            checkpoint_path = tmp_path / f"seed_{seed}.pt"
            # Create a dummy checkpoint file
            torch_mock = MagicMock()
            torch_mock.save = MagicMock()
            checkpoint_path.touch()
        
        with patch('src.models.aggregate_ensemble.load_checkpoint') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            models = load_model_checkpoints(tmp_path, seeds)
            
            assert len(models) == 3
            assert mock_load.call_count == 3

    def test_load_checkpoint_missing(self, tmp_path):
        """Test loading when checkpoint is missing."""
        with pytest.raises(FileNotFoundError):
            load_model_checkpoints(tmp_path, [1])
