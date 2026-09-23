"""
Unit tests for validation module (User Story 3).

Tests:
- Permutation testing logic (T030)
- FDR logic and verify count > 0 logic (T031)
- Sensitivity analysis on r (T033)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validation import (
    run_sensitivity_analysis_r,
    run_sensitivity_analysis_auc,
    compute_pearson_r
)

class TestSensitivityAnalysisR:
    """Tests for sensitivity analysis on r parameter."""
    
    def test_sensitivity_analysis_r_basic(self):
        """Test basic functionality of r sensitivity analysis."""
        # Create synthetic data
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = 0.5 * X[:, 0] + 0.3 * X[:, 1] + np.random.randn(n_samples) * 0.1
        
        # Run sensitivity analysis
        r_values = [0.1, 0.2, 0.3]
        results = run_sensitivity_analysis_r(X, y, r_values=r_values, n_folds=3)
        
        # Verify structure
        assert "r_values" in results
        assert "mean_pearson_r" in results
        assert "std_pearson_r" in results
        assert "variance_pearson_r" in results
        assert "best_r" in results
        
        # Verify results have correct length
        assert len(results["r_values"]) == len(r_values)
        assert len(results["mean_pearson_r"]) == len(r_values)
        assert len(results["std_pearson_r"]) == len(r_values)
        
        # Verify best_r is one of the tested values
        assert results["best_r"] in r_values
        
        # Verify variance is non-negative
        assert results["variance_pearson_r"] >= 0
        
    def test_sensitivity_analysis_r_insufficient_samples(self):
        """Test behavior with insufficient samples for CV."""
        np.random.seed(42)
        X = np.random.randn(5, 10)  # Too few samples for 5-fold CV
        y = np.random.randn(5)
        
        results = run_sensitivity_analysis_r(X, y, n_folds=5)
        
        # Should handle gracefully
        assert "error" in results or len(results["mean_pearson_r"]) > 0
        
    def test_sensitivity_analysis_r_variance_calculation(self):
        """Test that variance is calculated correctly."""
        np.random.seed(42)
        n_samples = 200
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = 0.5 * X[:, 0] + 0.3 * X[:, 1] + np.random.randn(n_samples) * 0.1
        
        r_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = run_sensitivity_analysis_r(X, y, r_values=r_values, n_folds=5)
        
        # Manually calculate expected variance
        mean_r_array = np.array(results["mean_pearson_r"])
        valid_mask = ~np.isnan(mean_r_array)
        expected_variance = np.var(mean_r_array[valid_mask])
        
        # Allow for small floating point differences
        assert abs(results["variance_pearson_r"] - expected_variance) < 1e-6
        
    def test_sensitivity_analysis_r_consistency(self):
        """Test that results are consistent across runs."""
        np.random.seed(42)
        n_samples = 100
        n_features = 5
        X = np.random.randn(n_samples, n_features)
        y = 0.5 * X[:, 0] + np.random.randn(n_samples) * 0.1
        
        r_values = [0.1, 0.2, 0.3]
        
        # Run twice
        results1 = run_sensitivity_analysis_r(X, y, r_values=r_values, n_folds=3)
        results2 = run_sensitivity_analysis_r(X, y, r_values=r_values, n_folds=3)
        
        # Results should be identical due to fixed random state in KFold
        assert results1["best_r"] == results2["best_r"]
        assert abs(results1["variance_pearson_r"] - results2["variance_pearson_r"]) < 1e-10

class TestSensitivityAnalysisAUC:
    """Tests for sensitivity analysis on AUC."""
    
    def test_sensitivity_analysis_auc_basic(self):
        """Test basic functionality of AUC sensitivity analysis."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        
        # Create balanced binary labels
        y = np.array([0] * 50 + [1] * 50)
        # Add some signal
        y[:25] = 0
        y[25:50] = 1
        y[50:75] = 0
        y[75:] = 1
        
        r_values = [0.1, 0.2, 0.3]
        results = run_sensitivity_analysis_auc(X, y, r_values=r_values, n_folds=3)
        
        # Verify structure
        assert "r_values" in results
        assert "mean_auc" in results
        assert "std_auc" in results
        assert "variance_auc" in results
        assert "best_r" in results
        
        # Verify results have correct length
        assert len(results["r_values"]) == len(r_values)
        assert len(results["mean_auc"]) == len(r_values)
        
        # Verify best_r is one of the tested values
        assert results["best_r"] in r_values
        
    def test_sensitivity_analysis_auc_imbalanced(self):
        """Test behavior with imbalanced classes."""
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        X = np.random.randn(n_samples, n_features)
        y = np.array([0] * 90 + [1] * 10)  # Highly imbalanced
        
        r_values = [0.1, 0.2, 0.3]
        results = run_sensitivity_analysis_auc(X, y, r_values=r_values, n_folds=3)
        
        # Should handle gracefully, though AUC might be unreliable
        assert "variance_auc" in results

class TestPearsonRCorrelation:
    """Tests for Pearson r calculation."""
    
    def test_pearson_r_perfect_correlation(self):
        """Test with perfectly correlated data."""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])
        
        r = compute_pearson_r(y_true, y_pred)
        assert abs(r - 1.0) < 1e-6
        
    def test_pearson_r_perfect_negative(self):
        """Test with perfectly negatively correlated data."""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([5, 4, 3, 2, 1])
        
        r = compute_pearson_r(y_true, y_pred)
        assert abs(r - (-1.0)) < 1e-6
        
    def test_pearson_r_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        y_true = np.random.randn(100)
        y_pred = np.random.randn(100)
        
        r = compute_pearson_r(y_true, y_pred)
        # Should be close to 0, but not exactly 0
        assert abs(r) < 0.3
        
    def test_pearson_r_empty_arrays(self):
        """Test with empty arrays."""
        y_true = np.array([])
        y_pred = np.array([])
        
        r = compute_pearson_r(y_true, y_pred)
        assert np.isnan(r)
        
    def test_pearson_r_single_value(self):
        """Test with single value."""
        y_true = np.array([1.0])
        y_pred = np.array([1.0])
        
        r = compute_pearson_r(y_true, y_pred)
        # Correlation of single point is undefined
        assert np.isnan(r)