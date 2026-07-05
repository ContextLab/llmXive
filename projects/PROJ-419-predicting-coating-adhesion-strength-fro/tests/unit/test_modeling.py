"""
Unit tests for User Story 2: Predictive Modeling and Feature Importance.
Specifically: SHAP value calculation and ranking stability.
"""

import os
import sys
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to path for imports if running directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.modeling import (
    load_processed_data,
    train_gradient_boosting,
    train_random_forest,
    compute_shap_values,
    compute_permutation_importance,
    rank_features,
    run_modeling_pipeline
)


class TestSHAPStability:
    """
    Tests for SHAP value calculation and ranking stability (T033).
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.test_dir, "test_data.csv")
        self.model_output_path = os.path.join(self.test_dir, "model_output.json")
        self.shap_output_path = os.path.join(self.test_dir, "shap_values.json")

        # Create a small, deterministic synthetic dataset for testing
        # This ensures reproducibility without relying on external data
        np.random.seed(42)
        n_samples = 100
        n_features = 5

        # Create deterministic features
        data = {
            'feature_1': np.random.rand(n_samples),
            'feature_2': np.random.rand(n_samples),
            'feature_3': np.random.rand(n_samples),
            'feature_4': np.random.rand(n_samples),
            'feature_5': np.random.rand(n_samples),
            'adhesion_strength': np.random.rand(n_samples) * 100  # Target variable
        }

        df = pd.DataFrame(data)
        df.to_csv(self.data_path, index=False)

        yield

        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_shap_values_are_computed_correctly(self):
        """
        Test that SHAP values are computed and have the correct shape.
        """
        # Train a simple model first
        X = pd.read_csv(self.data_path).drop('adhesion_strength', axis=1)
        y = pd.read_csv(self.data_path)['adhesion_strength']

        # Train a Random Forest model
        model = train_random_forest(X, y, n_estimators=10, max_depth=3)

        # Compute SHAP values
        shap_values, shap_summary = compute_shap_values(model, X)

        # Assertions
        assert shap_values is not None, "SHAP values should not be None"
        assert isinstance(shap_values, np.ndarray), "SHAP values should be a numpy array"
        assert shap_values.shape == X.shape, f"SHAP values shape {shap_values.shape} should match feature matrix shape {X.shape}"
        assert not np.all(shap_values == 0), "SHAP values should not be all zeros"

    def test_shap_ranking_stability(self):
        """
        Test that SHAP feature rankings are stable across multiple runs
        with the same data and model.
        """
        # Train a simple model
        X = pd.read_csv(self.data_path).drop('adhesion_strength', axis=1)
        y = pd.read_csv(self.data_path)['adhesion_strength']

        model = train_random_forest(X, y, n_estimators=10, max_depth=3)

        # Compute SHAP values multiple times
        shap_results = []
        for i in range(3):
            shap_vals, _ = compute_shap_values(model, X)
            # Calculate mean absolute SHAP value for each feature
            mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
            # Get ranking (indices sorted by importance)
            ranking = np.argsort(mean_abs_shap)[::-1]
            shap_results.append(ranking)

        # Check that rankings are identical across runs
        for i in range(1, len(shap_results)):
            assert np.array_equal(shap_results[0], shap_results[i]), \
                f"SHAP ranking should be stable across runs. Run 0: {shap_results[0]}, Run {i}: {shap_results[i]}"

    def test_shap_values_sum_to_prediction_difference(self):
        """
        Test that SHAP values sum to the difference between the model's
        prediction and the base value (a fundamental property of SHAP).
        """
        X = pd.read_csv(self.data_path).drop('adhesion_strength', axis=1)
        y = pd.read_csv(self.data_path)['adhesion_strength']

        model = train_random_forest(X, y, n_estimators=10, max_depth=3)

        # Compute SHAP values
        shap_values, _ = compute_shap_values(model, X)

        # Test on a single sample
        sample_idx = 0
        sample = X.iloc[sample_idx:sample_idx+1]

        # Get model prediction
        pred = model.predict(sample)[0]

        # Get base value (expected prediction on training data)
        base_value = np.mean(y)

        # Sum of SHAP values for this sample
        shap_sum = np.sum(shap_values[sample_idx])

        # The sum of SHAP values should approximately equal the difference
        # between the prediction and the base value
        # Note: Due to approximations in SHAP calculation, we allow some tolerance
        expected_diff = pred - base_value
        tolerance = 1.0  # Allow for some approximation error

        assert abs(shap_sum - expected_diff) < tolerance, \
            f"SHAP sum {shap_sum} should be close to prediction difference {expected_diff} (tolerance: {tolerance})"

    def test_rank_features_function(self):
        """
        Test the rank_features function produces consistent rankings.
        """
        X = pd.read_csv(self.data_path).drop('adhesion_strength', axis=1)
        y = pd.read_csv(self.data_path)['adhesion_strength']

        model = train_random_forest(X, y, n_estimators=10, max_depth=3)

        # Compute SHAP values
        shap_values, _ = compute_shap_values(model, X)

        # Rank features
        ranked_features, feature_importance = rank_features(shap_values, X.columns)

        # Assertions
        assert ranked_features is not None, "Ranked features should not be None"
        assert isinstance(ranked_features, list), "Ranked features should be a list"
        assert len(ranked_features) == len(X.columns), \
            f"Ranked features length {len(ranked_features)} should match number of features {len(X.columns)}"
        assert feature_importance is not None, "Feature importance should not be None"
        assert isinstance(feature_importance, dict), "Feature importance should be a dict"
        assert len(feature_importance) == len(X.columns), \
            f"Feature importance length {len(feature_importance)} should match number of features {len(X.columns)}"

    def test_shap_with_different_models(self):
        """
        Test that SHAP values can be computed for both Gradient Boosting and Random Forest.
        """
        X = pd.read_csv(self.data_path).drop('adhesion_strength', axis=1)
        y = pd.read_csv(self.data_path)['adhesion_strength']

        # Test with Random Forest
        rf_model = train_random_forest(X, y, n_estimators=10, max_depth=3)
        rf_shap, _ = compute_shap_values(rf_model, X)
        assert rf_shap is not None, "SHAP values for Random Forest should not be None"

        # Test with Gradient Boosting
        gb_model = train_gradient_boosting(X, y, n_estimators=10, max_depth=3)
        gb_shap, _ = compute_shap_values(gb_model, X)
        assert gb_shap is not None, "SHAP values for Gradient Boosting should not be None"

    def test_shap_output_structure(self):
        """
        Test that the SHAP summary output has the expected structure.
        """
        X = pd.read_csv(self.data_path).drop('adhesion_strength', axis=1)
        y = pd.read_csv(self.data_path)['adhesion_strength']

        model = train_random_forest(X, y, n_estimators=10, max_depth=3)

        shap_values, shap_summary = compute_shap_values(model, X)

        # Check that shap_summary is a dictionary with expected keys
        assert isinstance(shap_summary, dict), "SHAP summary should be a dictionary"
        assert 'feature_names' in shap_summary, "SHAP summary should contain 'feature_names'"
        assert 'mean_abs_shap' in shap_summary, "SHAP summary should contain 'mean_abs_shap'"
        assert 'ranking' in shap_summary, "SHAP summary should contain 'ranking'"

        # Verify feature_names match actual features
        assert shap_summary['feature_names'] == list(X.columns), \
            "SHAP summary feature_names should match actual feature names"

        # Verify ranking is a list of integers
        assert isinstance(shap_summary['ranking'], list), "SHAP summary ranking should be a list"
        assert all(isinstance(i, int) for i in shap_summary['ranking']), \
            "SHAP summary ranking should contain only integers"

    def test_ranking_stability_with_small_sample(self):
        """
        Test SHAP ranking stability with a very small sample size.
        """
        # Create a tiny dataset
        np.random.seed(123)
        tiny_data = {
            'f1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'f2': [0.5, 0.4, 0.3, 0.2, 0.1],
            'target': [10, 20, 30, 40, 50]
        }
        tiny_df = pd.DataFrame(tiny_data)
        tiny_path = os.path.join(self.test_dir, "tiny_data.csv")
        tiny_df.to_csv(tiny_path, index=False)

        X = tiny_df.drop('target', axis=1)
        y = tiny_df['target']

        model = train_random_forest(X, y, n_estimators=5, max_depth=2)

        # Run SHAP multiple times
        rankings = []
        for _ in range(5):
            shap_vals, _ = compute_shap_values(model, X)
            mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
            ranking = np.argsort(mean_abs_shap)[::-1]
            rankings.append(ranking)

        # All rankings should be identical
        for i in range(1, len(rankings)):
            assert np.array_equal(rankings[0], rankings[i]), \
                f"Ranking should be stable even with small samples. Run 0: {rankings[0]}, Run {i}: {rankings[i]}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])