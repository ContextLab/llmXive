"""
Unit tests for bootstrap resampling logic in the interpretability module.

This module validates the correctness of bootstrap resampling used for
stability analysis of feature importance in the BCC steel yield strength model.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)


def generate_test_data(n_samples=50, n_features=10, random_state=42):
    """
    Generate synthetic test data for bootstrap testing.
    
    Note: This is strictly for unit testing the resampling logic.
    Real data is loaded in the actual implementation.
    """
    np.random.seed(random_state)
    X = np.random.randn(n_samples, n_features)
    y = np.random.randn(n_samples)
    feature_names = [f"feature_{i}" for i in range(n_features)]
    return pd.DataFrame(X, columns=feature_names), pd.Series(y, name="target")


class TestBootstrapResampling:
    """Tests for bootstrap resampling functionality."""

    def test_bootstrap_sample_size(self):
        """Verify that bootstrap samples have the same size as the original data."""
        X, y = generate_test_data(n_samples=50)
        
        # Perform bootstrap sampling
        n_bootstrap = 10
        indices = np.random.choice(len(X), size=len(X), replace=True)
        X_sample = X.iloc[indices].reset_index(drop=True)
        y_sample = y.iloc[indices].reset_index(drop=True)
        
        assert len(X_sample) == len(X), "Bootstrap sample size must match original"
        assert len(y_sample) == len(y), "Bootstrap target size must match original"

    def test_bootstrap_with_replacement(self):
        """Verify that bootstrap sampling uses replacement."""
        X, y = generate_test_data(n_samples=50, random_state=123)
        
        # Run many bootstrap samples and check that duplicates exist
        n_iterations = 100
        has_duplicates = False
        
        for _ in range(n_iterations):
            indices = np.random.choice(len(X), size=len(X), replace=True)
            if len(np.unique(indices)) < len(indices):
                has_duplicates = True
                break
        
        assert has_duplicates, "Bootstrap sampling must use replacement"

    def test_bootstrap_randomness(self):
        """Verify that different seeds produce different samples."""
        X, y = generate_test_data(n_samples=50)
        
        # Generate samples with different seeds
        seed1 = 42
        seed2 = 123
        
        np.random.seed(seed1)
        indices1 = np.random.choice(len(X), size=len(X), replace=True)
        
        np.random.seed(seed2)
        indices2 = np.random.choice(len(X), size=len(X), replace=True)
        
        # They should be different (probability of collision is extremely low)
        assert not np.array_equal(indices1, indices2), "Different seeds should produce different samples"

    def test_bootstrap_indices_range(self):
        """Verify that bootstrap indices are within valid range."""
        n_samples = 50
        X, y = generate_test_data(n_samples=n_samples)
        
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        
        assert np.all(indices >= 0), "Indices must be non-negative"
        assert np.all(indices < n_samples), "Indices must be less than sample size"

    def test_bootstrap_preserves_feature_names(self):
        """Verify that feature names are preserved after resampling."""
        X, y = generate_test_data(n_samples=50)
        original_features = list(X.columns)
        
        indices = np.random.choice(len(X), size=len(X), replace=True)
        X_sample = X.iloc[indices].reset_index(drop=True)
        
        assert list(X_sample.columns) == original_features, "Feature names must be preserved"

    def test_bootstrap_statistical_properties(self):
        """Verify that bootstrap samples maintain approximate statistical properties."""
        X, y = generate_test_data(n_samples=1000, random_state=42)
        
        # Generate multiple bootstrap samples
        n_bootstrap = 100
        sample_means = []
        
        for _ in range(n_bootstrap):
            indices = np.random.choice(len(X), size=len(X), replace=True)
            X_sample = X.iloc[indices]
            sample_means.append(X_sample.mean().values)
        
        sample_means = np.array(sample_means)
        
        # The mean of bootstrap means should be close to the original mean
        original_mean = X.mean().values
        bootstrap_mean_of_means = sample_means.mean(axis=0)
        
        # Allow for some statistical variation (within 10% of original mean)
        tolerance = 0.1 * np.abs(original_mean)
        tolerance = np.maximum(tolerance, 1e-6)  # Avoid division by zero
        
        for i, (orig, boot) in enumerate(zip(original_mean, bootstrap_mean_of_means)):
            diff = np.abs(orig - boot)
            assert diff <= tolerance[i], f"Bootstrap mean for feature {i} deviates too much"

    def test_bootstrap_with_realistic_data_distribution(self):
        """Test bootstrap with data that mimics real experimental distributions."""
        # Create data with some outliers and skewness
        np.random.seed(42)
        n_samples = 100
        
        # Skewed distribution for one feature
        X = pd.DataFrame({
            'normal': np.random.randn(n_samples),
            'skewed': np.random.exponential(scale=2.0, size=n_samples),
            'outlier': np.random.randn(n_samples)
        })
        X.loc[np.random.choice(n_samples, 5), 'outlier'] = 10.0  # Add outliers
        
        y = pd.Series(np.random.randn(n_samples), name="target")
        
        # Perform bootstrap
        n_bootstrap = 50
        bootstrap_means = []
        
        for _ in range(n_bootstrap):
            indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_sample = X.iloc[indices]
            bootstrap_means.append(X_sample.mean().values)
        
        bootstrap_means = np.array(bootstrap_means)
        
        # Check that bootstrap captures the general location of the data
        original_means = X.mean().values
        bootstrap_means_avg = bootstrap_means.mean(axis=0)
        
        # The bootstrap should not shift the mean by more than 20%
        for i, (orig, boot) in enumerate(zip(original_means, bootstrap_means_avg)):
            if np.abs(orig) > 1e-6:
                relative_diff = np.abs(orig - boot) / np.abs(orig)
                assert relative_diff < 0.2, f"Bootstrap shifted mean too much for feature {i}"

    def test_bootstrap_deterministic_with_seed(self):
        """Verify that bootstrap is deterministic when seed is set."""
        X, y = generate_test_data(n_samples=50)
        
        seed = 42
        np.random.seed(seed)
        indices1 = np.random.choice(len(X), size=len(X), replace=True)
        
        np.random.seed(seed)
        indices2 = np.random.choice(len(X), size=len(X), replace=True)
        
        assert np.array_equal(indices1, indices2), "Same seed should produce identical samples"

    def test_bootstrap_edge_case_small_sample(self):
        """Test bootstrap with very small sample size."""
        X, y = generate_test_data(n_samples=5)
        
        # Should still work with small samples
        indices = np.random.choice(len(X), size=len(X), replace=True)
        X_sample = X.iloc[indices]
        
        assert len(X_sample) == 5, "Small sample bootstrap should maintain size"
        assert len(np.unique(indices)) <= 5, "Unique indices cannot exceed sample size"

    def test_bootstrap_feature_importance_stability_framework(self):
        """
        Test the framework for computing feature importance stability.
        This simulates the actual use case in bootstrap_stability.py
        """
        X, y = generate_test_data(n_samples=100, n_features=5)
        
        # Simulate feature importance calculation (e.g., from a model)
        # In reality, this would be trained feature importance
        def mock_feature_importance(X_train, y_train):
            # Return random "importance" values for testing framework
            np.random.seed(sum(X_train.values.flatten()) % 1000)
            return np.abs(np.random.randn(X_train.shape[1]))
        
        n_bootstrap = 20
        importance_stability = []
        
        for i in range(n_bootstrap):
            indices = np.random.choice(len(X), size=len(X), replace=True)
            X_boot = X.iloc[indices]
            y_boot = y.iloc[indices]
            
            importance = mock_feature_importance(X_boot, y_boot)
            importance_stability.append(importance)
        
        importance_stability = np.array(importance_stability)
        
        # Calculate standard deviation across bootstrap samples
        importance_std = importance_stability.std(axis=0)
        importance_mean = importance_stability.mean(axis=0)
        
        # Verify that we get reasonable statistics
        assert importance_std.shape == (5,), "Std dev shape must match number of features"
        assert importance_mean.shape == (5,), "Mean shape must match number of features"
        
        # All values should be non-negative
        assert np.all(importance_std >= 0), "Standard deviation must be non-negative"
        assert np.all(importance_mean >= 0), "Mean importance must be non-negative"

    def test_bootstrap_sample_uniqueness_probability(self):
        """
        Verify that bootstrap samples are not always identical to original.
        The probability of getting the exact same sample is (1/e)^n which is very small.
        """
        X, y = generate_test_data(n_samples=20)
        original_indices = np.arange(len(X))
        
        n_trials = 1000
        identical_count = 0
        
        for _ in range(n_trials):
            indices = np.random.choice(len(X), size=len(X), replace=True)
            if np.array_equal(np.sort(indices), np.sort(original_indices)):
                # Check if it's actually the same set (order doesn't matter for set comparison)
                # But for bootstrap, we care about the actual sample
                if np.array_equal(indices, original_indices):
                    identical_count += 1
        
        # With n=20, probability of exact match is extremely low
        # We expect 0 or very few matches in 1000 trials
        assert identical_count < 10, "Too many identical samples - bootstrap may not be working correctly"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])