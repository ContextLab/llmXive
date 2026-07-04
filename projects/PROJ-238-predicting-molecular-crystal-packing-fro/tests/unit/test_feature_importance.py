"""
Unit tests for permutation importance calculation.

This module validates the permutation importance logic used in
User Story 3 (Feature Importance, Sensitivity Analysis).
"""
import pytest
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.datasets import make_regression
import sys
import os

# Add parent directory to path to allow imports from code/utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.metrics import paired_t_test


def calculate_permutation_importance(model, X, y, metric_func=r2_score, n_repeats=5, random_state=42):
    """
    Calculate permutation importance for a fitted model.
    
    Parameters:
    -----------
    model : sklearn estimator
        Fitted model.
    X : array-like
        Feature matrix.
    y : array-like
        Target vector.
    metric_func : callable
        Function to compute performance (higher is better).
    n_repeats : int
        Number of times to permute a feature.
    random_state : int
        Random seed for reproducibility.
        
    Returns:
    --------
    dict
        Mapping of feature index to mean importance score.
    """
    base_score = metric_func(y, model.predict(X))
    importances = {}
    rng = np.random.RandomState(random_state)
    n_features = X.shape[1]
    
    for i in range(n_features):
        scores = []
        for _ in range(n_repeats):
            X_perm = X.copy()
            # Shuffle the i-th column
            perm_idx = rng.permutation(X.shape[0])
            X_perm[:, i] = X_perm[:, i][perm_idx]
            
            score = metric_func(y, model.predict(X_perm))
            scores.append(score)
        
        # Importance is the drop in performance
        importances[i] = base_score - np.mean(scores)
        
    return importances


class TestPermutationImportance:
    """Tests for the permutation importance calculation logic."""

    def test_importance_non_negative_with_noise(self):
        """
        Test that permutation importance is generally non-negative 
        when permuting relevant features in a noisy dataset.
        
        We expect that shuffling a feature that contributes to the 
        model's prediction will decrease performance (positive importance).
        """
        # Create a dataset with strong signal in first 3 features
        X, y = make_regression(
            n_samples=500, 
            n_features=10, 
            n_informative=3, 
            noise=0.1, 
            random_state=42
        )
        
        model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=5)
        model.fit(X, y)
        
        importances = calculate_permutation_importance(model, X, y, n_repeats=3)
        
        # The first 3 features should have positive importance on average
        # (though a single run might occasionally be negative due to noise, 
        # with n_repeats=3 and strong signal, it's highly likely)
        # We assert that the mean importance of informative features is > 0
        informative_importance = [importances[i] for i in range(3)]
        assert np.mean(informative_importance) > 0, \
            f"Mean importance of informative features should be positive, got {np.mean(informative_importance)}"

    def test_importance_zero_for_irrelevant_features(self):
        """
        Test that permuting irrelevant features results in near-zero importance.
        """
        # Create dataset where only first feature matters
        X, y = make_regression(
            n_samples=500, 
            n_features=10, 
            n_informative=1, 
            noise=0.0, 
            random_state=42
        )
        
        model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=5)
        model.fit(X, y)
        
        importances = calculate_permutation_importance(model, X, y, n_repeats=5)
        
        # Features 1-9 are irrelevant; their importance should be close to zero
        irrelevant_importance = [importances[i] for i in range(1, 10)]
        mean_irrelevant = np.mean(irrelevant_importance)
        
        # Allow small tolerance due to randomness in permutation
        assert abs(mean_irrelevant) < 0.05, \
            f"Mean importance of irrelevant features should be near zero, got {mean_irrelevant}"

    def test_importance_consistency(self):
        """
        Test that permutation importance is consistent across runs with same seed.
        """
        X, y = make_regression(
            n_samples=300, 
            n_features=5, 
            n_informative=3, 
            noise=0.2, 
            random_state=123
        )
        
        model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=4)
        model.fit(X, y)
        
        # Run twice with same seed
        imp1 = calculate_permutation_importance(model, X, y, n_repeats=3, random_state=99)
        imp2 = calculate_permutation_importance(model, X, y, n_repeats=3, random_state=99)
        
        # Results should be identical
        for i in range(5):
            assert imp1[i] == imp2[i], \
                f"Importance for feature {i} should be identical: {imp1[i]} vs {imp2[i]}"

    def test_importance_ranking(self):
        """
        Test that the most important feature is correctly identified.
        """
        # Create dataset where feature 0 has much higher coefficient
        X, y = make_regression(
            n_samples=500, 
            n_features=3, 
            n_informative=3, 
            noise=0.05, 
            random_state=42,
            coef=[10.0, 2.0, 1.0]  # Feature 0 is most important
        )
        
        model = RandomForestRegressor(n_estimators=20, random_state=42, max_depth=6)
        model.fit(X, y)
        
        importances = calculate_permutation_importance(model, X, y, n_repeats=5)
        
        # Feature 0 should have the highest importance
        max_idx = max(importances, key=importances.get)
        assert max_idx == 0, \
            f"Feature 0 should be most important, but feature {max_idx} was highest with {importances[max_idx]}"

    def test_importance_with_different_metrics(self):
        """
        Test that permutation importance works with different metric functions.
        """
        X, y = make_regression(
            n_samples=200, 
            n_features=4, 
            n_informative=2, 
            noise=0.1, 
            random_state=42
        )
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Test with R2 (default)
        imp_r2 = calculate_permutation_importance(model, X, y, metric_func=r2_score)
        
        # Test with negative MSE (higher is better, so we negate)
        from sklearn.metrics import mean_squared_error
        def neg_mse(y_true, y_pred):
            return -mean_squared_error(y_true, y_pred)
        
        imp_mse = calculate_permutation_importance(model, X, y, metric_func=neg_mse)
        
        # Both should identify the same top feature (feature 0 or 1)
        top_r2 = max(imp_r2, key=imp_r2.get)
        top_mse = max(imp_mse, key=imp_mse.get)
        
        assert top_r2 == top_mse, \
            f"Top feature should be consistent across metrics: R2={top_r2}, MSE={top_mse}"

    def test_importance_empty_features(self):
        """
        Test behavior with a single feature dataset.
        """
        X, y = make_regression(
            n_samples=100, 
            n_features=1, 
            noise=0.1, 
            random_state=42
        )
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        importances = calculate_permutation_importance(model, X, y)
        
        assert 0 in importances, "Should have importance for the single feature"
        # With a single informative feature, importance should be positive
        assert importances[0] > 0, "Single feature importance should be positive"

    def test_importance_type_consistency(self):
        """
        Test that importance values are floats.
        """
        X, y = make_regression(
            n_samples=100, 
            n_features=3, 
            noise=0.1, 
            random_state=42
        )
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        importances = calculate_permutation_importance(model, X, y)
        
        for key, value in importances.items():
            assert isinstance(value, (float, np.floating)), \
                f"Importance for feature {key} should be float, got {type(value)}"

    def test_permutation_does_not_modify_original_data(self):
        """
        Test that the original X matrix is not modified during calculation.
        """
        X, y = make_regression(
            n_samples=100, 
            n_features=3, 
            noise=0.1, 
            random_state=42
        )
        
        X_original = X.copy()
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        calculate_permutation_importance(model, X, y, n_repeats=2)
        
        # Check that X is unchanged
        assert np.array_equal(X, X_original), \
            "Original feature matrix should not be modified during permutation importance calculation"