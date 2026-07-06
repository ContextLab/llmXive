"""
Unit tests for feature importance extraction and p-value calculation.
Tests the Ridge regression model, cross-validation logic, and statistical inference.
"""
import pytest
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut, KFold
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from models import (
    get_cross_validation_split,
    run_ridge_regression,
    calculate_feature_pvalues,
    extract_feature_importance,
    get_top_features
)


class TestCrossValidationSplit:
    """Tests for the LOOCV vs 5-fold switch logic."""

    def test_small_dataset_uses_loocv(self):
        """Dataset with < 30 samples should use LOOCV."""
        cv_splitter, n_splits = get_cross_validation_split(29)
        assert isinstance(cv_splitter, LeaveOneOut)
        assert n_splits == 29

    def test_large_dataset_uses_kfold(self):
        """Dataset with >= 30 samples should use 5-fold CV."""
        cv_splitter, n_splits = get_cross_validation_split(30)
        assert isinstance(cv_splitter, KFold)
        assert cv_splitter.n_splits == 5
        assert n_splits == 5

    def test_very_large_dataset_uses_kfold(self):
        """Dataset with many samples should still use 5-fold CV."""
        cv_splitter, n_splits = get_cross_validation_split(1000)
        assert isinstance(cv_splitter, KFold)
        assert cv_splitter.n_splits == 5
        assert n_splits == 5


class TestRidgeRegression:
    """Tests for Ridge regression execution."""

    def test_ridge_regression_basic(self):
        """Test basic Ridge regression on synthetic data."""
        np.random.seed(42)
        n_samples, n_features = 50, 5
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        
        result = run_ridge_regression(X, y, alpha=1.0)
        
        assert 'r2_scores' in result
        assert 'mean_r2' in result
        assert 'std_r2' in result
        assert 'coef' in result
        assert len(result['r2_scores']) == 5  # 5-fold CV
        assert result['cv_type'] == '5-fold'

    def test_ridge_regression_small_dataset(self):
        """Test Ridge regression with small dataset (LOOCV)."""
        np.random.seed(42)
        n_samples, n_features = 10, 3
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        
        result = run_ridge_regression(X, y, alpha=1.0)
        
        assert len(result['r2_scores']) == 10  # LOOCV
        assert result['cv_type'] == 'LOOCV'

    def test_ridge_regression_empty_input(self):
        """Test that empty input raises ValueError."""
        X = np.array([]).reshape(0, 5)
        y = np.array([])
        
        with pytest.raises(ValueError, match="Input data is empty"):
            run_ridge_regression(X, y)


class TestPValueCalculation:
    """Tests for p-value calculation functionality."""

    def test_pvalue_calculation_basic(self):
        """Test basic p-value calculation."""
        np.random.seed(42)
        n_samples, n_features = 50, 3
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        feature_names = ['feat1', 'feat2', 'feat3']
        
        results = calculate_feature_pvalues(X, y, feature_names)
        
        assert len(results) == 3
        for name in feature_names:
            assert name in results
            coef, p_val = results[name]
            assert isinstance(coef, float)
            assert isinstance(p_val, float)
            assert 0 <= p_val <= 1

    def test_pvalue_calculation_small_dataset(self):
        """Test p-value calculation with insufficient degrees of freedom."""
        np.random.seed(42)
        n_samples, n_features = 3, 3
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        feature_names = ['feat1', 'feat2', 'feat3']
        
        results = calculate_feature_pvalues(X, y, feature_names)
        
        # Should return p-value of 1.0 when dof <= 0
        for name in feature_names:
            assert results[name][1] == 1.0

    def test_pvalue_calculation_mismatched_sizes(self):
        """Test that mismatched X and y sizes raise error."""
        X = np.random.randn(10, 5)
        y = np.random.randn(8)
        feature_names = ['f1', 'f2', 'f3', 'f4', 'f5']
        
        with pytest.raises(ValueError, match="X and y must have the same number of samples"):
            calculate_feature_pvalues(X, y, feature_names)


class TestFeatureImportance:
    """Tests for feature importance extraction."""

    def test_importance_extraction_basic(self):
        """Test basic feature importance extraction."""
        np.random.seed(42)
        n_samples, n_features = 50, 4
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        feature_names = ['a', 'b', 'c', 'd']
        
        importance = extract_feature_importance(X, y, feature_names, alpha=1.0)
        
        assert len(importance) == 4
        for name in feature_names:
            assert name in importance
            assert 'mean_coefficient' in importance[name]
            assert 'std_coefficient' in importance[name]
            assert 'p_value' in importance[name]

    def test_importance_extraction_consistency(self):
        """Test that importance values are consistent across runs."""
        np.random.seed(42)
        X = np.random.randn(40, 3)
        y = np.random.randn(40)
        feature_names = ['x1', 'x2', 'x3']
        
        imp1 = extract_feature_importance(X, y, feature_names)
        imp2 = extract_feature_importance(X, y, feature_names)
        
        for name in feature_names:
            assert imp1[name]['mean_coefficient'] == imp2[name]['mean_coefficient']
            assert imp1[name]['p_value'] == imp2[name]['p_value']


class TestTopFeatures:
    """Tests for top feature extraction."""

    def test_top_features_basic(self):
        """Test extraction of top features."""
        importance = {
            'feat1': {'mean_coefficient': 0.5, 'std_coefficient': 0.1, 'p_value': 0.01},
            'feat2': {'mean_coefficient': 2.0, 'std_coefficient': 0.2, 'p_value': 0.001},
            'feat3': {'mean_coefficient': -1.5, 'std_coefficient': 0.15, 'p_value': 0.05},
            'feat4': {'mean_coefficient': 0.1, 'std_coefficient': 0.05, 'p_value': 0.9}
        }
        
        top = get_top_features(importance, n_top=2)
        
        assert len(top) == 2
        # Should be feat2 (2.0) and feat3 (-1.5, abs=1.5)
        assert top[0][0] == 'feat2'
        assert top[1][0] == 'feat3'

    def test_top_features_n_top_greater_than_total(self):
        """Test when n_top is larger than available features."""
        importance = {
            'feat1': {'mean_coefficient': 0.5, 'std_coefficient': 0.1, 'p_value': 0.01},
            'feat2': {'mean_coefficient': 2.0, 'std_coefficient': 0.2, 'p_value': 0.001}
        }
        
        top = get_top_features(importance, n_top=5)
        
        assert len(top) == 2
        assert top[0][0] == 'feat2'
        assert top[1][0] == 'feat1'

    def test_top_features_empty_input(self):
        """Test with empty importance dictionary."""
        importance = {}
        top = get_top_features(importance, n_top=3)
        assert len(top) == 0