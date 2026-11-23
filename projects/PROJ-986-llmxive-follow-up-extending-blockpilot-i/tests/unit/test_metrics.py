"""
Unit tests for the metrics module.
"""
import pytest
import numpy as np
from code.utils.metrics import (
    calculate_latency,
    calculate_mean_latency,
    calculate_accuracy,
    calculate_regression_accuracy,
    calculate_mae,
    calculate_rmse,
    calculate_correlation,
    calculate_pcc,
    calculate_scc,
    calculate_kcc,
    calculate_r_squared
)


class TestLatency:
    def test_calculate_latency_returns_result_and_time(self):
        def dummy_func():
            return 42
        
        result, latency = calculate_latency(dummy_func)
        
        assert result == 42
        assert latency >= 0
        assert isinstance(latency, float)
    
    def test_calculate_latency_propagates_exception(self):
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            calculate_latency(failing_func)
    
    def test_mean_latency(self):
        def dummy_func():
            pass
        
        avg_latency = calculate_mean_latency(dummy_func, n_runs=3)
        assert avg_latency >= 0
        assert isinstance(avg_latency, float)


class TestAccuracy:
    def test_exact_accuracy(self):
        predictions = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 3, 4, 5]
        
        acc = calculate_accuracy(predictions, ground_truth)
        assert acc == 1.0
    
    def test_partial_accuracy(self):
        predictions = [1, 2, 3, 4, 5]
        ground_truth = [1, 2, 0, 4, 5]
        
        acc = calculate_accuracy(predictions, ground_truth)
        assert acc == 0.8
    
    def test_no_accuracy(self):
        predictions = [1, 2, 3]
        ground_truth = [4, 5, 6]
        
        acc = calculate_accuracy(predictions, ground_truth)
        assert acc == 0.0
    
    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError):
            calculate_accuracy([1, 2], [1])
    
    def test_empty_arrays(self):
        acc = calculate_accuracy([], [])
        assert acc == 0.0


class TestRegressionAccuracy:
    def test_within_tolerance(self):
        predictions = [1.0, 2.0, 3.0]
        ground_truth = [1.1, 2.1, 3.1]
        
        acc = calculate_regression_accuracy(predictions, ground_truth, tolerance=0.2)
        assert acc == 1.0
    
    def test_outside_tolerance(self):
        predictions = [1.0, 2.0, 3.0]
        ground_truth = [1.5, 2.5, 3.5]
        
        acc = calculate_regression_accuracy(predictions, ground_truth, tolerance=0.2)
        assert acc == 0.0


class TestMAE:
    def test_mae_basic(self):
        predictions = [1, 2, 3]
        ground_truth = [1, 3, 3]
        
        mae = calculate_mae(predictions, ground_truth)
        assert mae == pytest.approx(1/3, rel=1e-5)
    
    def test_mae_zero(self):
        mae = calculate_mae([1, 2], [1, 2])
        assert mae == 0.0


class TestRMSE:
    def test_rmse_basic(self):
        predictions = [1, 2, 3]
        ground_truth = [1, 3, 3]
        
        rmse = calculate_rmse(predictions, ground_truth)
        # sqrt((0 + 1 + 0)/3) = sqrt(1/3)
        assert rmse == pytest.approx(np.sqrt(1/3), rel=1e-5)
    
    def test_rmse_zero(self):
        rmse = calculate_rmse([1, 2], [1, 2])
        assert rmse == 0.0


class TestCorrelation:
    def test_pearson_perfect_positive(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        
        corr, p_val = calculate_pcc(x, y)
        assert corr == pytest.approx(1.0, rel=1e-5)
        assert p_val < 0.05
    
    def test_pearson_perfect_negative(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 4, 3, 2, 1]
        
        corr, p_val = calculate_pcc(x, y)
        assert corr == pytest.approx(-1.0, rel=1e-5)
    
    def test_spearman_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        
        corr, p_val = calculate_scc(x, y)
        assert corr == pytest.approx(1.0, rel=1e-5)
    
    def test_kendall_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        
        corr, p_val = calculate_kcc(x, y)
        assert corr == pytest.approx(1.0, rel=1e-5)
    
    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError):
            calculate_correlation([1, 2], [1])
    
    def test_constant_array(self):
        x = [1, 1, 1]
        y = [1, 2, 3]
        
        corr, p_val = calculate_correlation(x, y)
        assert corr == 0.0
    
    def test_invalid_method_raises(self):
        with pytest.raises(ValueError):
            calculate_correlation([1, 2], [1, 2], method='invalid')


class TestRSquared:
    def test_r_squared_perfect(self):
        predictions = [1, 2, 3]
        ground_truth = [1, 2, 3]
        
        r2 = calculate_r_squared(predictions, ground_truth)
        assert r2 == 1.0
    
    def test_r_squared_zero(self):
        predictions = [2, 2, 2]
        ground_truth = [1, 2, 3]
        
        r2 = calculate_r_squared(predictions, ground_truth)
        # SS_res = 1+0+1 = 2, SS_tot = 1+0+1 = 2, R2 = 0
        assert r2 == pytest.approx(0.0, rel=1e-5)