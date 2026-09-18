"""
Unit tests for threshold sweep logic in sensitivity analysis.

Tests verify that:
1. The sensitivity sweep iterates over the correct threshold values
2. Model retraining with different thresholds produces varying results
3. The variation calculation correctly identifies the max R² difference
4. Edge cases (empty thresholds, single threshold) are handled properly
"""

import os
import sys
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modeling.eval import run_sensitivity_sweep, calculate_variation
from config import load_config, get_config


class TestSensitivitySweepLogic:
    """Tests for the threshold sweep logic in sensitivity analysis."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = MagicMock()
        config.bgc_threshold = 0.5
        config.sensitivity_thresholds = [0.1, 0.3, 0.5, 0.7]
        config.data_path = Path("data")
        config.processed_path = Path("data/processed")
        config.interim_path = Path("data/interim")
        return config

    @pytest.fixture
    def mock_pca_features(self):
        """Create mock PCA features data."""
        np.random.seed(42)
        n_samples = 50
        n_features = 10
        
        data = np.random.randn(n_samples, n_features)
        species = [f"Species_{i}" for i in range(n_samples)]
        
        df = pd.DataFrame(data, columns=[f"PC{i+1}" for i in range(n_features)])
        df.insert(0, "species", species)
        
        return df

    @pytest.fixture
    def mock_aligned_data(self):
        """Create mock aligned data with BGC and metabolite information."""
        np.random.seed(42)
        n_samples = 50
        
        data = {
            "species": [f"Species_{i}" for i in range(n_samples)],
            "bgc_count": np.random.randint(0, 10, n_samples),
            "metabolite_abundance": np.random.rand(n_samples) * 100,
            "clade": np.random.choice(["Clade_A", "Clade_B", "Clade_C"], n_samples)
        }
        
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_model_results(self):
        """Create mock model results for different thresholds."""
        return {
            "threshold_0.1": {"r2": 0.45, "rmse": 12.3, "mae": 8.7},
            "threshold_0.3": {"r2": 0.52, "rmse": 10.1, "mae": 7.2},
            "threshold_0.5": {"r2": 0.48, "rmse": 11.5, "mae": 8.0},
            "threshold_0.7": {"r2": 0.41, "rmse": 13.8, "mae": 9.5}
        }

    def test_sweep_iterates_correct_thresholds(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test that the sweep iterates over the correct threshold values."""
        thresholds = [0.1, 0.3, 0.5, 0.7]
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        # Setup mock to return different R² for each threshold
                        mock_retrain.side_effect = [
                            {"r2": 0.45, "rmse": 12.3},
                            {"r2": 0.52, "rmse": 10.1},
                            {"r2": 0.48, "rmse": 11.5},
                            {"r2": 0.41, "rmse": 13.8}
                        ]
                        
                        results = run_sensitivity_sweep(thresholds)
                        
                        # Verify that retrain_with_thresholds was called for each threshold
                        assert mock_retrain.call_count == len(thresholds)
                        
                        # Verify that results contain entries for each threshold
                        assert len(results) == len(thresholds)
                        
                        for threshold in thresholds:
                            key = f"threshold_{threshold}"
                            assert key in results
                            assert "r2" in results[key]
    
    def test_sweep_produces_varying_results(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test that different thresholds produce different model results."""
        thresholds = [0.1, 0.3, 0.5, 0.7]
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        # Setup mock to return significantly different R² values
                        mock_retrain.side_effect = [
                            {"r2": 0.30, "rmse": 15.0},
                            {"r2": 0.60, "rmse": 8.0},
                            {"r2": 0.45, "rmse": 11.0},
                            {"r2": 0.35, "rmse": 14.0}
                        ]
                        
                        results = run_sensitivity_sweep(thresholds)
                        
                        # Extract R² values
                        r2_values = [results[key]["r2"] for key in results.keys()]
                        
                        # Verify that R² values are not all identical
                        assert len(set(r2_values)) > 1, "All thresholds produced identical R² values"
                        
                        # Verify that the range of R² values is significant
                        r2_range = max(r2_values) - min(r2_values)
                        assert r2_range > 0.1, f"R² variation ({r2_range:.3f}) is too small"
    
    def test_single_threshold(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test that the sweep handles a single threshold correctly."""
        thresholds = [0.5]
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        mock_retrain.return_value = {"r2": 0.50, "rmse": 10.0}
                        
                        results = run_sensitivity_sweep(thresholds)
                        
                        assert len(results) == 1
                        assert "threshold_0.5" in results
                        assert results["threshold_0.5"]["r2"] == 0.50
    
    def test_empty_thresholds(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test that the sweep handles empty thresholds list."""
        thresholds = []
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    results = run_sensitivity_sweep(thresholds)
                    
                    assert len(results) == 0
    
    def test_threshold_order_preserved(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test that the order of thresholds is preserved in results."""
        thresholds = [0.7, 0.1, 0.5, 0.3]  # Unsorted order
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        mock_retrain.return_value = {"r2": 0.50, "rmse": 10.0}
                        
                        results = run_sensitivity_sweep(thresholds)
                        
                        # Check that keys are created in the order of thresholds
                        expected_keys = [f"threshold_{t}" for t in thresholds]
                        actual_keys = list(results.keys())
                        
                        assert actual_keys == expected_keys, f"Order not preserved: {actual_keys} != {expected_keys}"

class TestCalculateVariation:
    """Tests for the variation calculation function."""

    def test_calculate_variation_basic(self, mock_model_results):
        """Test basic variation calculation."""
        r2_values = [result["r2"] for result in mock_model_results.values()]
        expected_max_diff = max(r2_values) - min(r2_values)
        
        max_diff, variation_result = calculate_variation(mock_model_results)
        
        assert np.isclose(max_diff, expected_max_diff)
        assert "max_r2_difference" in variation_result
        assert np.isclose(variation_result["max_r2_difference"], expected_max_diff)
    
    def test_calculate_variation_single_threshold(self):
        """Test variation calculation with a single threshold."""
        results = {
            "threshold_0.5": {"r2": 0.50, "rmse": 10.0}
        }
        
        max_diff, variation_result = calculate_variation(results)
        
        assert max_diff == 0.0
        assert variation_result["max_r2_difference"] == 0.0
        assert variation_result["passes_sensitivity_check"] is True
    
    def test_calculate_variation_empty_results(self):
        """Test variation calculation with empty results."""
        results = {}
        
        max_diff, variation_result = calculate_variation(results)
        
        assert max_diff == 0.0
        assert "error" in variation_result
        assert variation_result["passes_sensitivity_check"] is False
    
    def test_calculate_variation_threshold_check(self):
        """Test that the threshold check (≤ 0.05) is correctly applied."""
        # Case 1: Variation within threshold
        results_pass = {
            "threshold_0.1": {"r2": 0.50, "rmse": 10.0},
            "threshold_0.5": {"r2": 0.52, "rmse": 9.8}
        }
        
        _, variation_result_pass = calculate_variation(results_pass)
        assert variation_result_pass["passes_sensitivity_check"] is True
        assert variation_result_pass["max_r2_difference"] <= 0.05
        
        # Case 2: Variation exceeds threshold
        results_fail = {
            "threshold_0.1": {"r2": 0.50, "rmse": 10.0},
            "threshold_0.5": {"r2": 0.60, "rmse": 8.0}
        }
        
        _, variation_result_fail = calculate_variation(results_fail)
        assert variation_result_fail["passes_sensitivity_check"] is False
        assert variation_result_fail["max_r2_difference"] > 0.05
    
    def test_calculate_variation_negative_r2(self):
        """Test variation calculation with negative R² values."""
        results = {
            "threshold_0.1": {"r2": -0.10, "rmse": 15.0},
            "threshold_0.5": {"r2": 0.30, "rmse": 10.0}
        }
        
        max_diff, variation_result = calculate_variation(results)
        
        expected_max_diff = 0.30 - (-0.10)
        assert np.isclose(max_diff, expected_max_diff)
        assert variation_result["passes_sensitivity_check"] is False
    
    def test_calculate_variation_with_nan(self):
        """Test variation calculation with NaN values."""
        results = {
            "threshold_0.1": {"r2": float('nan'), "rmse": 15.0},
            "threshold_0.5": {"r2": 0.50, "rmse": 10.0}
        }
        
        max_diff, variation_result = calculate_variation(results)
        
        # NaN should be handled gracefully
        assert "error" in variation_result or np.isnan(max_diff)

class TestIntegrationSensitivitySweep:
    """Integration tests for the sensitivity sweep workflow."""

    def test_end_to_end_sweep_workflow(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test the complete end-to-end sensitivity sweep workflow."""
        thresholds = [0.1, 0.3, 0.5, 0.7]
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        # Simulate realistic variation in R² values
                        r2_values = [0.45, 0.52, 0.48, 0.41]
                        mock_retrain.side_effect = [
                            {"r2": r2, "rmse": 12.0 - i * 0.5}
                            for i, r2 in enumerate(r2_values)
                        ]
                        
                        # Run the sweep
                        sweep_results = run_sensitivity_sweep(thresholds)
                        
                        # Calculate variation
                        max_diff, variation_result = calculate_variation(sweep_results)
                        
                        # Verify the workflow completed successfully
                        assert len(sweep_results) == len(thresholds)
                        assert "max_r2_difference" in variation_result
                        assert max_diff == variation_result["max_r2_difference"]
                        
                        # Verify that the max difference matches expected
                        expected_max_diff = max(r2_values) - min(r2_values)
                        assert np.isclose(max_diff, expected_max_diff)
    
    def test_sweep_with_realistic_data_patterns(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test sweep with realistic data patterns (non-monotonic R² variation)."""
        thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        # Simulate realistic pattern: R² increases then decreases
        # (optimal threshold in the middle)
        realistic_r2 = [0.35, 0.48, 0.55, 0.50, 0.40]
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        mock_retrain.side_effect = [
                            {"r2": r2, "rmse": 15.0 - i * 1.5}
                            for i, r2 in enumerate(realistic_r2)
                        ]
                        
                        sweep_results = run_sensitivity_sweep(thresholds)
                        
                        # Verify all thresholds are present
                        assert len(sweep_results) == len(thresholds)
                        
                        # Extract R² values
                        r2_values = [sweep_results[f"threshold_{t}"]["r2"] for t in thresholds]
                        
                        # Verify the pattern: peak at threshold 0.5
                        peak_idx = np.argmax(r2_values)
                        assert thresholds[peak_idx] == 0.5
                        
                        # Verify that the variation is within expected range
                        max_diff = max(r2_values) - min(r2_values)
                        assert 0.1 < max_diff < 0.3  # Reasonable variation for realistic data
    
    def test_sweep_handles_retrain_failures_gracefully(self, mock_config, mock_pca_features, mock_aligned_data):
        """Test that the sweep handles retraining failures gracefully."""
        thresholds = [0.1, 0.3, 0.5]
        
        with patch("modeling.eval.load_config", return_value=mock_config):
            with patch("modeling.eval.load_pca_features", return_value=mock_pca_features):
                with patch("modeling.eval.load_aligned_data", return_value=mock_aligned_data):
                    with patch("modeling.eval.retrain_with_thresholds") as mock_retrain:
                        # Simulate failure for one threshold
                        mock_retrain.side_effect = [
                            {"r2": 0.45, "rmse": 12.0},
                            Exception("Training failed for threshold 0.3"),
                            {"r2": 0.40, "rmse": 13.0}
                        ]
                        
                        # The sweep should continue and collect results for successful runs
                        # Note: In a real implementation, this might skip failed thresholds or log errors
                        results = run_sensitivity_sweep(thresholds)
                        
                        # Verify that at least some results were collected
                        assert len(results) >= 1
                        
                        # Verify that the successful thresholds are present
                        assert "threshold_0.1" in results
                        assert "threshold_0.5" in results