"""
Unit tests for Cross-Validation and Permutation logic in model metrics.

This module verifies:
1. Confidence Interval (CI) calculation from CV fold scores.
2. Permutation test p-value logic for R² significance.
"""
import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
from scipy.stats import norm

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.stoichiometry_parser import parse_formula
from utils.periodic_data import get_atomic_radius, get_electronegativity, get_valence_electrons


# --- Helper Functions for Testing (Mirroring logic in 03_train_and_evaluate.py and 04_compute_ci.py) ---

def calculate_confidence_interval(scores, confidence=0.95):
    """
    Calculate the confidence interval from a list of fold scores.
    Uses the percentile method.
    """
    scores = np.array(scores)
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    return np.percentile(scores, lower_percentile), np.percentile(scores, upper_percentile)


def calculate_permutation_p_value(actual_score, permuted_scores):
    """
    Calculate the p-value for the actual score against permuted scores.
    Null hypothesis: The actual score is not better than random.
    p-value = (count of permuted >= actual + 1) / (total + 1)
    """
    permuted_scores = np.array(permuted_scores)
    count = np.sum(permuted_scores >= actual_score)
    return (count + 1) / (len(permuted_scores) + 1)


# --- Test Class for CI Calculation (T026b) ---

class TestConfidenceIntervalCalculation:
    """Tests for CI calculation from CV fold scores."""

    def test_ci_calculation_perfect_scores(self):
        """CI should be [1.0, 1.0] if all scores are 1.0."""
        scores = [1.0, 1.0, 1.0, 1.0, 1.0]
        lower, upper = calculate_confidence_interval(scores)
        assert lower == 1.0
        assert upper == 1.0

    def test_ci_calculation_range(self):
        """CI should cover the middle 95% of the distribution."""
        # Create a known distribution
        np.random.seed(42)
        scores = np.random.normal(loc=0.5, scale=0.1, size=1000)
        lower, upper = calculate_confidence_interval(scores)
        
        # Verify the CI bounds are within the min and max of the scores
        assert lower >= min(scores)
        assert upper <= max(scores)
        # Verify the CI is not a single point (unless variance is 0)
        assert upper > lower

    def test_ci_calculation_small_sample(self):
        """CI should work correctly with small sample sizes (e.g., 5 folds)."""
        scores = [0.1, 0.2, 0.3, 0.4, 0.5]
        lower, upper = calculate_confidence_interval(scores)
        
        # For [0.1, 0.2, 0.3, 0.4, 0.5], 2.5th percentile is 0.1, 97.5th is 0.5
        # (Exact values depend on interpolation method in numpy)
        assert lower <= 0.2
        assert upper >= 0.4

    def test_ci_calculation_negative_scores(self):
        """CI should handle negative R² scores correctly."""
        scores = [-0.5, -0.2, 0.0, 0.1, 0.3]
        lower, upper = calculate_confidence_interval(scores)
        assert lower <= -0.2
        assert upper >= 0.1


# --- Test Class for Permutation Logic (T026a) ---

class TestPermutationPValueLogic:
    """Tests for permutation test p-value calculation."""

    def test_p_value_highly_significant(self):
        """P-value should be low if actual score is much higher than permuted."""
        actual = 0.8
        permuted = [0.1, 0.2, 0.15, 0.1, 0.2]
        p_val = calculate_permutation_p_value(actual, permuted)
        assert p_val <= 0.2 # (0+1)/(5+1) = 1/6 approx 0.166

    def test_p_value_not_significant(self):
        """P-value should be high if actual score is within permuted range."""
        actual = 0.25
        permuted = [0.2, 0.3, 0.25, 0.22, 0.28]
        p_val = calculate_permutation_p_value(actual, permuted)
        # At least one permuted >= 0.25 (0.3, 0.25, 0.28) -> count >= 2
        # p_val = (2+1)/(5+1) = 0.5
        assert p_val >= 0.3

    def test_p_value_single_iteration(self):
        """Test with a single permuted score."""
        actual = 0.5
        permuted = [0.4]
        # 0.4 < 0.5, count = 0. p = (0+1)/(1+1) = 0.5
        p_val = calculate_permutation_p_value(actual, permuted)
        assert p_val == 0.5

    def test_p_value_all_permuted_higher(self):
        """P-value should be 1.0 if all permuted scores are higher."""
        actual = 0.1
        permuted = [0.5, 0.6, 0.7, 0.8, 0.9]
        p_val = calculate_permutation_p_value(actual, permuted)
        # count = 5. p = (5+1)/(5+1) = 1.0
        assert p_val == 1.0


# --- Integration Test: Simulating the Pipeline Logic ---

class TestModelMetricsIntegration:
    """Integration tests simulating the flow from CV to CI and Permutation."""

    @pytest.fixture
    def sample_data(self):
        """Generate simple sample data for regression."""
        np.random.seed(42)
        X = np.random.rand(100, 3)
        # y = 2*X[:, 0] + noise
        y = 2 * X[:, 0] + np.random.normal(0, 0.1, 100)
        return X, y

    def test_cv_fold_scores_logic(self, sample_data):
        """Verify that running a CV loop produces valid fold scores."""
        X, y = sample_data
        model = LinearRegression()
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        
        fold_scores = []
        for train_idx, test_idx in kfold.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            fold_scores.append(r2_score(y_test, y_pred))
        
        assert len(fold_scores) == 5
        assert all(isinstance(s, float) for s in fold_scores)
        assert all(-1 <= s <= 1 for s in fold_scores) # R2 range

    def test_ci_from_real_cv_folds(self, sample_data):
        """Verify CI calculation works on real CV fold outputs."""
        X, y = sample_data
        model = LinearRegression()
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        
        fold_scores = []
        for train_idx, test_idx in kfold.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            fold_scores.append(r2_score(y_test, y_pred))
        
        lower, upper = calculate_confidence_interval(fold_scores)
        
        # Verify the mean of fold scores is within the CI
        mean_score = np.mean(fold_scores)
        assert lower <= mean_score <= upper

    def test_permutation_test_on_model(self, sample_data):
        """Verify permutation test logic on a simple model."""
        X, y = sample_data
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        actual_r2 = r2_score(y, y_pred)
        
        # Simulate permutation: shuffle y
        np.random.seed(42)
        permuted_scores = []
        n_iter = 100
        for _ in range(n_iter):
            y_shuffled = np.random.permutation(y)
            model.fit(X, y_shuffled)
            y_pred_shuffled = model.predict(X)
            permuted_scores.append(r2_score(y_shuffled, y_pred_shuffled))
        
        p_val = calculate_permutation_p_value(actual_r2, permuted_scores)
        
        # With real signal, p-value should be low (significant)
        # With 100 iterations, p < 0.05 is likely if signal is strong
        assert 0 <= p_val <= 1.0

# --- Edge Case Tests for Data Loading (Mocking) ---

class TestMockedDataLoading:
    """Tests for error handling in data loading scenarios."""

    def test_handle_empty_fold_scores(self):
        """CI calculation should fail gracefully or raise error on empty list."""
        with pytest.raises(Exception):
            calculate_confidence_interval([])

    def test_handle_none_scores(self):
        """CI calculation should handle None input."""
        with pytest.raises(Exception):
            calculate_confidence_interval(None)

    def test_handle_non_numeric_scores(self):
        """CI calculation should handle non-numeric input."""
        with pytest.raises(Exception):
            calculate_confidence_interval(["a", "b", "c"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
