import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.analysis.validation import (
    load_null_residuals,
    run_freedman_lane_permutation,
    run_cross_validation,
)


class TestLoadNullResiduals:
    def test_loads_correctly(self):
        """Test that null residuals are loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            residuals_path = Path(tmpdir) / "null_residuals.csv"
            residuals = [0.1, -0.2, 0.3, -0.1, 0.05]
            df = pd.DataFrame({'residual': residuals})
            df.to_csv(residuals_path, index=False)

            result = load_null_residuals(str(residuals_path))

            assert isinstance(result, np.ndarray)
            assert len(result) == len(residuals)
            np.testing.assert_array_almost_equal(result, residuals)

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_null_residuals("/nonexistent/path/residuals.csv")

    def test_handles_empty_file(self):
        """Test behavior with empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            residuals_path = Path(tmpdir) / "null_residuals.csv"
            df = pd.DataFrame()
            df.to_csv(residuals_path, index=False)

            with pytest.raises((ValueError, IndexError)):
                load_null_residuals(str(residuals_path))


class TestRunFreedmanLanePermutation:
    def test_returns_expected_shape(self):
        """Test that permutation returns expected number of samples."""
        residuals = np.array([0.1, -0.2, 0.3, -0.1, 0.05, 0.2, -0.15, 0.1, -0.05, 0.25])
        observed_coef = 0.5
        n_permutations = 100
        seed = 42

        null_dist, p_value = run_freedman_lane_permutation(
            residuals, observed_coef, n_permutations, seed
        )

        assert len(null_dist) == n_permutations
        assert 0 <= p_value <= 1

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with fixed seed."""
        residuals = np.array([0.1, -0.2, 0.3, -0.1, 0.05, 0.2, -0.15, 0.1, -0.05, 0.25])
        observed_coef = 0.5
        n_permutations = 50
        seed = 42

        null_dist1, p_value1 = run_freedman_lane_permutation(
            residuals, observed_coef, n_permutations, seed
        )
        null_dist2, p_value2 = run_freedman_lane_permutation(
            residuals, observed_coef, n_permutations, seed
        )

        np.testing.assert_array_equal(null_dist1, null_dist2)
        assert p_value1 == p_value2

    def test_p_value_logic(self):
        """Test that p-value calculation follows correct logic."""
        # Create a case where observed coef is extreme
        residuals = np.array([0.0] * 100)
        observed_coef = 100.0  # Very extreme value
        n_permutations = 100
        seed = 42

        _, p_value = run_freedman_lane_permutation(
            residuals, observed_coef, n_permutations, seed
        )

        # With such an extreme observed value, p-value should be very small
        assert p_value <= 0.01

    def test_handles_small_sample(self):
        """Test behavior with very small sample size."""
        residuals = np.array([0.1, -0.2])
        observed_coef = 0.5
        n_permutations = 10
        seed = 42

        null_dist, p_value = run_freedman_lane_permutation(
            residuals, observed_coef, n_permutations, seed
        )

        assert len(null_dist) == n_permutations
        assert 0 <= p_value <= 1


class TestRunCrossValidation:
    def test_returns_expected_keys(self):
        """Test that CV results contain expected keys."""
        # Create mock data
        n_samples = 50
        n_features = 3

        X = np.random.randn(n_samples, n_features)
        y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n_samples) * 0.1

        cv_folds = 5
        seed = 42

        results = run_cross_validation(X, y, cv_folds, seed)

        assert isinstance(results, dict)
        assert 'mean_r2' in results
        assert 'std_r2' in results
        assert 'mean_rmse' in results
        assert 'std_rmse' in results

    def test_r2_bounds(self):
        """Test that R2 values are within reasonable bounds."""
        n_samples = 50
        n_features = 3

        X = np.random.randn(n_samples, n_features)
        y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n_samples) * 0.1

        cv_folds = 5
        seed = 42

        results = run_cross_validation(X, y, cv_folds, seed)

        # R2 can be negative for very bad models, but should be reasonable
        assert -10 <= results['mean_r2'] <= 1.0
        assert results['std_r2'] >= 0

    def test_rmse_positive(self):
        """Test that RMSE values are positive."""
        n_samples = 50
        n_features = 3

        X = np.random.randn(n_samples, n_features)
        y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n_samples) * 0.1

        cv_folds = 5
        seed = 42

        results = run_cross_validation(X, y, cv_folds, seed)

        assert results['mean_rmse'] > 0
        assert results['std_rmse'] >= 0

    def test_deterministic_with_seed(self):
        """Test that CV results are deterministic with fixed seed."""
        np.random.seed(42)
        n_samples = 50
        n_features = 3

        X = np.random.randn(n_samples, n_features)
        y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n_samples) * 0.1

        cv_folds = 5
        seed = 42

        results1 = run_cross_validation(X, y, cv_folds, seed)
        results2 = run_cross_validation(X, y, cv_folds, seed)

        assert results1['mean_r2'] == results2['mean_r2']
        assert results1['std_r2'] == results2['std_r2']
        assert results1['mean_rmse'] == results2['mean_rmse']
        assert results1['std_rmse'] == results2['std_rmse']

    def test_handles_small_dataset(self):
        """Test behavior with dataset smaller than folds."""
        n_samples = 3
        n_features = 2

        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)

        cv_folds = 5
        seed = 42

        # Should handle gracefully, possibly by reducing folds or raising error
        # Depending on implementation, this might raise an error
        try:
            results = run_cross_validation(X, y, cv_folds, seed)
            # If it runs, results should be valid
            assert isinstance(results, dict)
        except ValueError:
            # Expected behavior if implementation requires n_samples >= cv_folds
            pass
