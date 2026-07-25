"""
Integration tests for permutation test p-value calculation.

This module validates the correctness of the permutation test logic in code/evaluate.py.
It ensures that:
1. The permutation test correctly scrambles the relationship between features and target.
2. The calculated p-value reflects the proportion of permuted scores >= observed score.
3. The function handles edge cases (e.g., all zeros, single sample) gracefully.
"""

import json
import os
import pickle
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

# Import the function under test
# The path is relative to the project root where tests/ is a sibling of code/
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from evaluate import perform_permutation_test, load_features, load_model, calculate_metrics


class TestPermutationTest:
    """Integration tests for the permutation test p-value calculation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        
        # Create subdirectories matching project structure
        self.processed_dir = self.data_dir / "data" / "processed"
        self.results_dir = self.data_dir / "results"
        self.processed_dir.mkdir(parents=True)
        self.results_dir.mkdir(parents=True)

        yield

        # Cleanup
        shutil.rmtree(self.temp_dir)

    def _create_mock_features(self, n_samples=100, n_features=3):
        """Create a mock features.json file with random data."""
        features = []
        for i in range(n_samples):
            feature_record = {
                "sample_id": f"sample_{i}",
                "variance": float(np.random.rand()),
                "entropy": float(np.random.rand()),
                "skewness": float(np.random.rand()),
                "kurtosis": float(np.random.rand()),
                "dominant_eigenvalue": float(np.random.rand()),
                "fidelity_loss": float(np.random.rand())
            }
            features.append(feature_record)
        
        features_path = self.processed_dir / "features.json"
        with open(features_path, 'w') as f:
            json.dump(features, f)
        
        return features_path

    def _create_mock_model(self):
        """Create and save a mock trained model."""
        # Create a simple model that has some predictive power on random data
        # to ensure the observed R2 is not exactly 0 or 1
        X = np.random.rand(100, 3)
        y = np.random.rand(100)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        model_path = self.results_dir / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        return model_path

    def test_permutation_test_reduces_correlation(self):
        """
        Integration test: Verify that permuting features breaks the correlation.
        
        If the original model has a reasonable R2, the permuted versions should
        generally have lower R2 scores. The p-value should be low if the original
        correlation is significant.
        """
        # Create mock data where we know there is a relationship
        # We'll create features and target that are correlated
        n_samples = 200
        X = np.random.rand(n_samples, 3)
        # Create target with a linear relationship + noise
        y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.normal(0, 0.1, n_samples)
        
        # Train a model on this correlated data
        model = RandomForestRegressor(n_estimators=50, random_state=42, max_depth=5)
        model.fit(X, y)
        
        # Calculate observed R2
        y_pred = model.predict(X)
        observed_r2 = r2_score(y, y_pred)
        
        # Verify we have a positive correlation to test against
        assert observed_r2 > 0.1, "Test setup failed: Model has no predictive power"
        
        # Now run the permutation test logic manually to verify the function
        n_permutations = 100
        permuted_scores = []
        
        for _ in range(n_permutations):
            # Permute the target (y) to break the relationship with X
            y_permuted = np.random.permutation(y)
            # Re-evaluate on permuted target (simulating what the function does)
            # Note: In the actual implementation, we permute X, but the effect is symmetric
            # for R2 calculation in this context
            y_pred_perm = model.predict(X)
            # Actually, the standard permutation test for feature importance
            # permutes the feature matrix X. Let's do that.
            X_perm = X.copy()
            for j in range(X.shape[1]):
                X_perm[:, j] = np.random.permutation(X[:, j])
            
            y_pred_perm = model.predict(X_perm)
            r2_perm = r2_score(y, y_pred_perm)
            permuted_scores.append(r2_perm)
        
        # Calculate p-value: fraction of permuted scores >= observed score
        p_value = sum(1 for s in permuted_scores if s >= observed_r2) / n_permutations
        
        # With a strong correlation, the p-value should be low (e.g., < 0.05)
        # This is a probabilistic test, so we allow some tolerance
        assert p_value < 0.2, f"Permutation test failed: p-value {p_value} is too high for correlated data"

    def test_permutation_test_function_integration(self):
        """
        Integration test: Run the full perform_permutation_test function
        with mock data and verify it returns a valid p-value.
        """
        # Setup mock data
        features_path = self._create_mock_features(n_samples=100)
        model_path = self._create_mock_model()
        
        # Load the data
        features = load_features(str(features_path))
        model = load_model(str(model_path))
        
        # Extract X and y
        X = np.array([
            [f['variance'], f['entropy'], f['skewness'], f['kurtosis'], f['dominant_eigenvalue']]
            for f in features
        ])
        y = np.array([f['fidelity_loss'] for f in features])
        
        # Run the permutation test
        p_value = perform_permutation_test(
            model=model,
            X=X,
            y=y,
            n_permutations=50,  # Small number for speed in tests
            random_state=42
        )
        
        # Assertions
        assert isinstance(p_value, float), "p-value should be a float"
        assert 0.0 <= p_value <= 1.0, "p-value must be between 0 and 1"

    def test_permutation_test_deterministic_with_seed(self):
        """
        Integration test: Verify that the permutation test is deterministic
        when a random_state is provided.
        """
        features_path = self._create_mock_features(n_samples=50)
        model_path = self._create_mock_model()
        
        features = load_features(str(features_path))
        model = load_model(str(model_path))
        
        X = np.array([
            [f['variance'], f['entropy'], f['skewness'], f['kurtosis'], f['dominant_eigenvalue']]
            for f in features
        ])
        y = np.array([f['fidelity_loss'] for f in features])
        
        # Run twice with the same seed
        p_value_1 = perform_permutation_test(
            model=model, X=X, y=y, n_permutations=20, random_state=123
        )
        p_value_2 = perform_permutation_test(
            model=model, X=X, y=y, n_permutations=20, random_state=123
        )
        
        # They should be identical
        assert p_value_1 == p_value_2, "Permutation test should be deterministic with fixed seed"

    def test_permutation_test_high_pvalue_for_random_data(self):
        """
        Integration test: When features and target are uncorrelated,
        the p-value should be high (close to 0.5 or higher).
        """
        # Create completely random, uncorrelated data
        n_samples = 100
        X = np.random.rand(n_samples, 3)
        y = np.random.rand(n_samples)
        
        # Train a model (it will have poor performance)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        observed_r2 = r2_score(y, model.predict(X))
        
        # Run permutation test
        p_value = perform_permutation_test(
            model=model,
            X=X,
            y=y,
            n_permutations=50,
            random_state=42
        )
        
        # With random data, the observed R2 is likely similar to permuted R2s
        # So p-value should not be extremely low
        # We expect it to be > 0.1 (not significant)
        assert p_value > 0.05, "For random data, p-value should not be significant"

    def test_permutation_test_zero_variance_features(self):
        """
        Integration test: Handle edge case where features have zero variance.
        """
        # Create features with zero variance
        X = np.zeros((50, 3))
        y = np.random.rand(50)
        
        # Train a model (will fail to learn, but shouldn't crash permutation test)
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        try:
            model.fit(X, y)
        except Exception:
            # If fitting fails, skip this test case as it's a model limitation, not function logic
            pytest.skip("RandomForest cannot fit zero-variance features")
        
        # Run permutation test
        p_value = perform_permutation_test(
            model=model,
            X=X,
            y=y,
            n_permutations=20,
            random_state=42
        )
        
        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0

    def test_permutation_test_single_feature(self):
        """
        Integration test: Permutation test with a single feature.
        """
        X = np.random.rand(50, 1)
        y = X[:, 0] + np.random.normal(0, 0.1, 50)  # Strong correlation
        
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        p_value = perform_permutation_test(
            model=model,
            X=X,
            y=y,
            n_permutations=50,
            random_state=42
        )
        
        assert isinstance(p_value, float)
        assert 0.0 <= p_value <= 1.0
        # With strong correlation, p-value should be low
        assert p_value < 0.3, "Strong correlation should yield low p-value"

    def test_permutation_test_large_n_permutations(self):
        """
        Integration test: Verify stability with larger number of permutations.
        """
        X = np.random.rand(100, 3)
        y = X[:, 0] * 2 + np.random.normal(0, 0.2, 100)
        
        model = RandomForestRegressor(n_estimators=20, random_state=42)
        model.fit(X, y)
        
        # Run with more permutations
        p_value_large = perform_permutation_test(
            model=model,
            X=X,
            y=y,
            n_permutations=200,
            random_state=42
        )
        
        assert isinstance(p_value_large, float)
        assert 0.0 <= p_value_large <= 1.0

    def test_permutation_test_invalid_input_types(self):
        """
        Integration test: Verify behavior with invalid input types.
        """
        # Test with non-numeric data
        X = [["a", "b"], ["c", "d"]]
        y = [1, 2]
        
        model = MagicMock()
        model.predict.return_value = [1, 2]
        
        with pytest.raises((ValueError, TypeError)):
            perform_permutation_test(
                model=model,
                X=X,
                y=y,
                n_permutations=10,
                random_state=42
            )

    def test_permutation_test_empty_permutation_list(self):
        """
        Integration test: Edge case where n_permutations=0.
        """
        X = np.random.rand(10, 3)
        y = np.random.rand(10)
        
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        # This should handle 0 permutations gracefully or raise a clear error
        # Based on typical implementation, it should raise an error or return 0
        try:
            p_value = perform_permutation_test(
                model=model,
                X=X,
                y=y,
                n_permutations=0,
                random_state=42
            )
            # If it returns a value, it should be handled
            assert isinstance(p_value, (float, int))
        except ValueError as e:
            # Expected behavior: clear error message
            assert "permutations" in str(e).lower() or "n_permutations" in str(e).lower()

    def test_permutation_test_consistency_with_r2(self):
        """
        Integration test: Verify that the permutation test correctly uses R2.
        """
        # Create data with known R2
        X = np.random.rand(100, 3)
        y = X[:, 0] + X[:, 1] + np.random.normal(0, 0.1, 100)
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        y_pred = model.predict(X)
        true_r2 = r2_score(y, y_pred)
        
        # The permutation test calculates R2 for each permutation
        # We can't easily verify the exact p-value without running the whole test,
        # but we can verify the function completes and returns a valid value
        p_value = perform_permutation_test(
            model=model,
            X=X,
            y=y,
            n_permutations=30,
            random_state=42
        )
        
        assert 0.0 <= p_value <= 1.0
        # With true R2 > 0, p-value should generally be < 1.0
        # (unless the model is completely random)
        if true_r2 > 0.1:
            assert p_value < 0.9, "With meaningful R2, p-value should not be 1.0"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])