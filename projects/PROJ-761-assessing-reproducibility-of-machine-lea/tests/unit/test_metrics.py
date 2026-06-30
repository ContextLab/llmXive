"""
Unit tests for code/metrics.py
"""
import pytest
import numpy as np
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from metrics import (
    calculate_mae,
    calculate_r2,
    calculate_spearman_rho,
    calculate_deviation_index,
    calculate_all_metrics,
    EPSILON
)

class TestMAE:
    def test_perfect_prediction(self):
        y_true = [1.0, 2.0, 3.0]
        y_pred = [1.0, 2.0, 3.0]
        assert calculate_mae(y_true, y_pred) == 0.0

    def test_constant_error(self):
        y_true = [1.0, 2.0, 3.0]
        y_pred = [2.0, 3.0, 4.0]
        assert calculate_mae(y_true, y_pred) == 1.0

    def test_numpy_arrays(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        assert calculate_mae(y_true, y_pred) == 0.5

    def test_empty_array(self):
        y_true = []
        y_pred = []
        assert calculate_mae(y_true, y_pred) == 0.0

    def test_shape_mismatch(self):
        y_true = [1.0, 2.0]
        y_pred = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            calculate_mae(y_true, y_pred)

class TestR2:
    def test_perfect_prediction(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert calculate_r2(y_true, y_pred) == 1.0

    def test_worse_than_mean(self):
        y_true = [1.0, 2.0, 3.0]
        y_pred = [3.0, 2.0, 1.0]  # Inverted trend
        r2 = calculate_r2(y_true, y_pred)
        assert r2 < 0.0

    def test_constant_prediction(self):
        y_true = [1.0, 2.0, 3.0]
        y_pred = [2.0, 2.0, 2.0]  # Mean prediction
        assert calculate_r2(y_true, y_pred) == 0.0

    def test_empty_array(self):
        y_true = []
        y_pred = []
        assert calculate_r2(y_true, y_pred) == 0.0

    def test_shape_mismatch(self):
        y_true = [1.0, 2.0]
        y_pred = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            calculate_r2(y_true, y_pred)

class TestSpearmanRho:
    def test_perfect_correlation(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert calculate_spearman_rho(y_true, y_pred) == 1.0

    def test_perfect_negative_correlation(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [5.0, 4.0, 3.0, 2.0, 1.0]
        assert calculate_spearman_rho(y_true, y_pred) == -1.0

    def test_no_correlation(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [5.0, 1.0, 3.0, 2.0, 4.0]
        rho = calculate_spearman_rho(y_true, y_pred)
        assert abs(rho) < 1.0  # Should not be perfect

    def test_empty_array(self):
        y_true = []
        y_pred = []
        assert calculate_spearman_rho(y_true, y_pred) == 0.0

    def test_single_element(self):
        y_true = [1.0]
        y_pred = [2.0]
        assert calculate_spearman_rho(y_true, y_pred) == 0.0

    def test_shape_mismatch(self):
        y_true = [1.0, 2.0]
        y_pred = [1.0, 2.0, 3.0]
        with pytest.raises(ValueError):
            calculate_spearman_rho(y_true, y_pred)

class TestDeviationIndex:
    def test_perfect_agreement(self):
        # When observed equals reference, S should be 1.0
        s = calculate_deviation_index(
            mae_obs=1.0, r2_obs=0.9, rho_obs=0.8,
            mae_ref=1.0, r2_ref=0.9, rho_ref=0.8
        )
        assert abs(s - 1.0) < 1e-6

    def test_zero_reference_values(self):
        # Test handling of zero reference values with epsilon
        s = calculate_deviation_index(
            mae_obs=0.1, r2_obs=0.0, rho_obs=0.0,
            mae_ref=0.0, r2_ref=0.0, rho_ref=0.0
        )
        # Should not raise error, S should be < 1.0
        assert s < 1.0

    def test_negative_reference_values(self):
        # R2 and rho can be negative
        s = calculate_deviation_index(
            mae_obs=1.0, r2_obs=-0.5, rho_obs=-0.2,
            mae_ref=1.0, r2_ref=-0.5, rho_ref=-0.2
        )
        assert abs(s - 1.0) < 1e-6

    def test_epsilon_usage(self):
        # Verify epsilon prevents division by zero
        s = calculate_deviation_index(
            mae_obs=0.0001, r2_obs=0.0, rho_obs=0.0,
            mae_ref=0.0, r2_ref=0.0, rho_ref=0.0,
            epsilon=EPSILON
        )
        assert s < 1.0

class TestCalculateAllMetrics:
    def test_basic_calculation(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.2, 4.8]
        
        metrics = calculate_all_metrics(y_true, y_pred)
        
        assert "mae" in metrics
        assert "r2" in metrics
        assert "spearman_rho" in metrics
        assert "deviation_index" not in metrics  # No refs provided

    def test_with_references(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.2, 4.8]
        
        mae_ref = calculate_mae(y_true, y_pred)
        r2_ref = calculate_r2(y_true, y_pred)
        rho_ref = calculate_spearman_rho(y_true, y_pred)
        
        metrics = calculate_all_metrics(
            y_true, y_pred,
            mae_ref, r2_ref, rho_ref
        )
        
        assert "deviation_index" in metrics
        assert abs(metrics["deviation_index"] - 1.0) < 1e-4  # Allow small numerical error

    def test_partial_references(self):
        y_true = [1.0, 2.0, 3.0, 4.0, 5.0]
        y_pred = [1.1, 2.1, 2.9, 4.2, 4.8]
        
        # Provide only some references
        metrics = calculate_all_metrics(
            y_true, y_pred,
            mae_ref=1.0  # Only MAE ref
        )
        
        assert "deviation_index" not in metrics  # Should only calculate if all provided

if __name__ == "__main__":
    pytest.main([__file__, "-v"])