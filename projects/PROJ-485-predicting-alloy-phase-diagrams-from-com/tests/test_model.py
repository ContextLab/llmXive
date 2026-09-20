"""
Test suite for User Story 2: Model Training and Cross-Validation.
Implements mandatory tests for power analysis and LOSO logic.
"""
import pytest
import sys
import os
import json
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock, Mock

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.error_codes import ErrorCode
from models.train import perform_power_analysis


class TestPowerAnalysis:
    """
    Tests for power analysis logic as required by FR-014 and T023.
    """

    def _create_mock_loso_results(self, n_folds=5, mae_values=None):
        """Helper to create mock LOSO results structure."""
        if mae_values is None:
            mae_values = [100.0, 105.0, 98.0, 102.0, 99.0]
        
        return {
            "folds": [
                {
                    "fold_id": f"fold_{i}",
                    "train_size": 100,
                    "test_size": 20,
                    "mae": mae_values[i],
                    "r2": 0.85,
                    "elements_in_test": ["Cu", "Zn"],
                    "elements_in_train": ["Cu", "Zn", "Al", "Fe"]
                }
                for i in range(n_folds)
            ],
            "aggregate": {
                "mean_mae": sum(mae_values) / len(mae_values),
                "std_mae": np.std(mae_values)
            }
        }

    def test_power_analysis_insufficient(self):
        """
        Asserting INSUFFICIENT_POWER is raised when power < 0.8 (Mandatory per FR-014).
        
        This test simulates a scenario where the effect size is small or sample size
        is insufficient, resulting in a calculated power < 0.8.
        """
        # Mock data that results in low power
        # We simulate a scenario where the effect size (difference from null) is tiny
        # relative to the variance, or the sample size is too small.
        # In perform_power_analysis, we calculate power based on:
        # alpha=0.05, power_target=0.8, effect_size (Cohen's d), n (sample size)
        
        # Create a mock result set with very high variance or low effect size
        # Let's assume the null model MAE is 100.0, and our RF model MAE is 99.9 (tiny improvement)
        # Variance is high.
        
        mock_loso_results = self._create_mock_loso_results(
            n_folds=3, 
            mae_values=[100.0, 100.1, 99.9] # Very small difference
        )
        
        # Mock the null baseline results to have similar MAE (low effect size)
        mock_null_results = {
            "mean_mae": 100.0,
            "std_mae": 50.0 # High variance
        }

        # We need to patch the statsmodels or the internal calculation to force a low power
        # Since perform_power_analysis likely uses statsmodels.stats.power, we mock that.
        
        with patch('models.train.TTestIndPower') as mock_power_class:
            # Simulate a power calculation that returns < 0.8
            mock_solver = MagicMock()
            mock_solver.solve_power = MagicMock(return_value=0.5) # Simulated power = 0.5
            mock_power_class.return_value = mock_solver

            # Also mock the load_loso_results to return our mock data
            with patch('models.train.load_loso_results', return_value=mock_loso_results):
                with patch('models.train.load_null_results', return_value=mock_null_results):
                    with pytest.raises(Exception) as exc_info:
                        perform_power_analysis(
                            loso_results_path="dummy_path",
                            null_results_path="dummy_path",
                            output_path="dummy_path"
                        )
                    
                    # Verify the exception type or message contains the error code
                    # The implementation should raise an exception or log the error code
                    # Based on T023 description: "halt with INSUFFICIENT_POWER if failed"
                    
                    # Check if the error code is present in the exception message or type
                    error_msg = str(exc_info.value)
                    assert "INSUFFICIENT_POWER" in error_msg or ErrorCode.INSUFFICIENT_POWER in error_msg, \
                        f"Expected INSUFFICIENT_POWER error, got: {error_msg}"

    def test_power_analysis_sufficient(self):
        """
        Asserting no exception is raised when power >= 0.8.
        """
        mock_loso_results = self._create_mock_loso_results(
            n_folds=5,
            mae_values=[50.0, 52.0, 48.0, 51.0, 49.0] # Good improvement over null
        )
        
        mock_null_results = {
            "mean_mae": 100.0,
            "std_mae": 10.0 # Low variance, high effect size
        }

        with patch('models.train.TTestIndPower') as mock_power_class:
            # Simulate a power calculation that returns >= 0.8
            mock_solver = MagicMock()
            mock_solver.solve_power = MagicMock(return_value=0.95)
            mock_power_class.return_value = mock_solver

            with patch('models.train.load_loso_results', return_value=mock_loso_results):
                with patch('models.train.load_null_results', return_value=mock_null_results):
                    # This should not raise an exception
                    try:
                        perform_power_analysis(
                            loso_results_path="dummy_path",
                            null_results_path="dummy_path",
                            output_path="dummy_path"
                        )
                    except Exception as e:
                        pytest.fail(f"perform_power_analysis raised unexpected exception: {e}")

    def test_power_analysis_edge_case_boundary(self):
        """
        Test behavior exactly at the 0.8 threshold.
        """
        mock_loso_results = self._create_mock_loso_results()
        mock_null_results = {"mean_mae": 100.0, "std_mae": 10.0}

        with patch('models.train.TTestIndPower') as mock_power_class:
            mock_solver = MagicMock()
            mock_solver.solve_power = MagicMock(return_value=0.80) # Exactly 0.8
            mock_power_class.return_value = mock_solver

            with patch('models.train.load_loso_results', return_value=mock_loso_results):
                with patch('models.train.load_null_results', return_value=mock_null_results):
                    # Should pass (>= 0.8)
                    try:
                        perform_power_analysis(
                            loso_results_path="dummy_path",
                            null_results_path="dummy_path",
                            output_path="dummy_path"
                        )
                    except Exception as e:
                        pytest.fail(f"Power analysis should pass at exactly 0.8, got: {e}")