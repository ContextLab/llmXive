"""
Unit tests for T020 baseline comparison logic.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np
import torch

# Add code to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from metrics.baseline_comparison import (
    compute_zero_delta_mse,
    perform_statistical_test,
    run_baseline_comparison
)
from models.gru_estimator import GRUEstimator

class TestBaselineComparison:
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a mock dataframe with required columns."""
        np.random.seed(42)
        n_samples = 100
        data = {
            "latent_delta_magnitude": np.random.randn(n_samples) * 2.0,
            "feature_1": np.random.randn(n_samples),
            "feature_2": np.random.randn(n_samples),
            "feature_3": np.random.randn(n_samples)
        }
        return pd.DataFrame(data)

    def test_compute_zero_delta_mse(self, sample_dataframe):
        """Test that zero-delta MSE is the variance of the target."""
        mse = compute_zero_delta_mse(sample_dataframe)
        expected_mse = np.mean(sample_dataframe["latent_delta_magnitude"] ** 2)
        assert np.isclose(mse, expected_mse)

    def test_perform_statistical_test_no_model(self, sample_dataframe):
        """Test stats result when model is absent."""
        result = perform_statistical_test(sample_dataframe, model_preds=None)
        assert result["t_statistic"] is None
        assert result["p_value"] is None
        assert result["significant_at_0.05"] is None

    def test_perform_statistical_test_with_model(self, sample_dataframe):
        """Test stats result with valid model predictions."""
        # Create random predictions that are slightly better than zero
        y_true = sample_dataframe["latent_delta_magnitude"].values
        # Add some noise but keep correlation
        model_preds = y_true * 0.8 + np.random.randn(len(y_true)) * 0.1
        
        result = perform_statistical_test(sample_dataframe, model_preds)
        
        assert result["t_statistic"] is not None
        assert result["p_value"] is not None
        assert isinstance(result["significant_at_0.05"], bool)

    def test_run_baseline_comparison_integration(self, sample_dataframe, tmp_path):
        """
        Integration test: Run the full script logic with mocked data and model.
        """
        # Setup temporary directories
        data_dir = tmp_path / "data" / "processed"
        metrics_dir = tmp_path / "data" / "metrics"
        models_dir = tmp_path / "data" / "models"
        data_dir.mkdir(parents=True)
        metrics_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)
        
        # Save mock parquet
        parquet_path = data_dir / "final_dataset.parquet"
        sample_dataframe.to_parquet(parquet_path)
        
        # Create a dummy model checkpoint
        model = GRUEstimator(input_size=3, hidden_size=64, output_size=2)
        checkpoint_path = models_dir / "estimator_checkpoint.pt"
        torch.save({
            "model_state_dict": model.state_dict()
        }, checkpoint_path)
        
        # Mock the paths in the module
        with patch("metrics.baseline_comparison.PROJECT_ROOT", tmp_path), \
             patch("metrics.baseline_comparison.PROCESSED_DATA_PATH", parquet_path), \
             patch("metrics.baseline_comparison.MODEL_CHECKPOINT_PATH", checkpoint_path), \
             patch("metrics.baseline_comparison.DATA_METRICS_DIR", metrics_dir):
            
            # Run the function
            import argparse
            args = argparse.Namespace(seed=42)
            run_baseline_comparison(args)
            
            # Verify output exists
            output_path = metrics_dir / "baseline_comparison.json"
            assert output_path.exists()
            
            with open(output_path) as f:
                result = json.load(f)
            
            assert "zero_delta_mse" in result
            assert "model_mse" in result
            assert result["model_mse"] is not None
            assert result["status"] == "completed"