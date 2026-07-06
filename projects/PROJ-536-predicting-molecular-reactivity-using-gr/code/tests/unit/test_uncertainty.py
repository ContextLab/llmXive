"""
Unit tests for Conformal Prediction logic.
"""
import pytest
import numpy as np
import pandas as pd
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

from src.analysis.uncertainty import (
    calculate_conformal_scores,
    generate_prediction_intervals,
    calculate_coverage_rate,
    run_conformal_prediction
)

class TestConformalBounds:
    """Tests for the Conformal Prediction interval generation."""

    def test_calculate_conformal_scores_basic(self):
        """Test basic score calculation."""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([10.0, 20.0, 30.0])
        
        # Mock data
        data = pd.DataFrame({
            'features': [np.array([1, 2]), np.array([3, 4]), np.array([5, 6])],
            'yield': [12.0, 18.0, 32.0]
        })
        
        scores = calculate_conformal_scores(mock_model, data)
        
        # Expected: |12-10|=2, |18-20|=2, |32-30|=2
        expected_scores = np.array([2.0, 2.0, 2.0])
        np.testing.assert_array_almost_equal(scores, expected_scores)

    def test_generate_prediction_intervals_structure(self):
        """Test that intervals are generated with correct columns."""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([10.0, 20.0])
        
        # Mock data
        data = pd.DataFrame({
            'features': [np.array([1, 2]), np.array([3, 4])],
            'yield': [12.0, 18.0]
        })
        
        # Mock scores
        scores = np.array([2.0, 2.0, 2.0])
        
        result = generate_prediction_intervals(mock_model, data, scores, alpha=0.1)
        
        assert 'pred_lower' in result.columns
        assert 'pred_upper' in result.columns
        assert 'pred_point' in result.columns
        assert 'true_yield' in result.columns
        assert len(result) == 2

    def test_coverage_rate_calculation(self):
        """Test coverage rate calculation."""
        data = pd.DataFrame({
            'true_yield': [10.0, 20.0, 30.0, 40.0],
            'pred_lower': [5.0, 15.0, 35.0, 35.0],
            'pred_upper': [15.0, 25.0, 25.0, 45.0]
        })
        # True values: 10 (in), 20 (in), 30 (out), 40 (in) -> 3/4 = 0.75
        
        coverage = calculate_coverage_rate(data)
        assert abs(coverage - 0.75) < 1e-6

    def test_coverage_rate_perfect(self):
        """Test perfect coverage."""
        data = pd.DataFrame({
            'true_yield': [10.0, 20.0],
            'pred_lower': [0.0, 0.0],
            'pred_upper': [100.0, 100.0]
        })
        coverage = calculate_coverage_rate(data)
        assert abs(coverage - 1.0) < 1e-6

    def test_coverage_rate_zero(self):
        """Test zero coverage."""
        data = pd.DataFrame({
            'true_yield': [10.0, 20.0],
            'pred_lower': [15.0, 25.0],
            'pred_upper': [30.0, 35.0]
        })
        coverage = calculate_coverage_rate(data)
        assert abs(coverage - 0.0) < 1e-6

    @patch('src.analysis.uncertainty.load_model_and_data')
    @patch('src.analysis.uncertainty.calculate_conformal_scores')
    @patch('src.analysis.uncertainty.generate_prediction_intervals')
    @patch('src.analysis.uncertainty.calculate_coverage_rate')
    @patch('src.analysis.uncertainty.save_uncertainty_results')
    def test_run_conformal_prediction_flow(
        self, mock_save, mock_cov, mock_gen_int, mock_calc_scores, mock_load
    ):
        """Test the full orchestration flow."""
        # Setup mocks
        mock_model = MagicMock()
        mock_data = pd.DataFrame({'features': [np.array([1])], 'yield': [10.0]})
        mock_load.return_value = (mock_model, mock_data)
        mock_calc_scores.return_value = np.array([1.0])
        
        mock_result_df = pd.DataFrame({
            'features': [np.array([1])],
            'yield': [10.0],
            'pred_lower': [8.0],
            'pred_upper': [12.0],
            'pred_point': [10.0],
            'true_yield': [10.0]
        })
        mock_gen_int.return_value = mock_result_df
        mock_cov.return_value = 1.0
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "results")
            os.makedirs(output_path, exist_ok=True)
            
            metrics = run_conformal_prediction(
                model_path="fake.pt",
                data_path="fake.csv",
                output_dir=output_path,
                calibration_split=0.5,
                alpha=0.1,
                seed=42
            )
            
            assert 'empirical_coverage' in metrics
            assert metrics['empirical_coverage'] == 1.0
            mock_save.assert_called_once()