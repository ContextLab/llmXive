"""Unit tests for the collinearity filter logic in code/04_train_model.py.

This test suite verifies that the CollinearityTransformer correctly identifies
pairs of features with Pearson correlation > 0.95 and drops the one with
lower variance, keeping the higher-variance feature.
"""
import numpy as np
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.stats import calculate_pearson_correlation
from code.utils.stats import check_collinearity


class TestCollinearityFilter:
    """Tests for the collinearity filtering logic."""

    def test_no_high_correlation(self):
        """When no features have correlation > 0.95, all features should be kept."""
        # Create features with low correlation
        np.random.seed(42)
        n_samples = 100
        X = np.random.randn(n_samples, 3)
        # Make features slightly correlated but not above threshold
        X[:, 1] = X[:, 0] * 0.5 + np.random.randn(n_samples) * 0.5
        X[:, 2] = X[:, 1] * 0.3 + np.random.randn(n_samples) * 0.7

        feature_names = [f"feat_{i}" for i in range(3)]
        df = pd.DataFrame(X, columns=feature_names)

        # Check collinearity
        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        assert len(kept_features) == 3
        assert len(dropped_features) == 0
        assert set(kept_features) == set(feature_names)

    def test_perfectly_correlated_pair(self):
        """When two features are perfectly correlated (>0.95), the lower-variance one should be dropped."""
        np.random.seed(42)
        n_samples = 100
        base = np.random.randn(n_samples)

        # Feature 0: high variance
        feat_0 = base * 10.0 + np.random.randn(n_samples) * 0.1
        # Feature 1: low variance, perfectly correlated with feat_0
        feat_1 = base * 1.0 + np.random.randn(n_samples) * 0.1

        X = np.column_stack([feat_0, feat_1])
        feature_names = ["high_var_feat", "low_var_feat"]
        df = pd.DataFrame(X, columns=feature_names)

        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        # Should keep high variance, drop low variance
        assert len(kept_features) == 1
        assert len(dropped_features) == 1
        assert kept_features[0] == "high_var_feat"
        assert dropped_features[0] == "low_var_feat"

    def test_correlation_just_above_threshold(self):
        """Features with correlation just above 0.95 should trigger the filter."""
        np.random.seed(42)
        n_samples = 200
        base = np.random.randn(n_samples)

        # Create two features with correlation ~0.96
        feat_0 = base * 5.0 + np.random.randn(n_samples) * 2.0
        feat_1 = base * 5.0 + np.random.randn(n_samples) * 1.0  # Slightly less noise -> higher corr

        X = np.column_stack([feat_0, feat_1])
        feature_names = ["feat_a", "feat_b"]
        df = pd.DataFrame(X, columns=feature_names)

        # Verify correlation is above threshold
        corr = calculate_pearson_correlation(df["feat_a"], df["feat_b"])
        assert corr > 0.95, f"Test setup failed: correlation {corr} is not > 0.95"

        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        assert len(kept_features) == 1
        assert len(dropped_features) == 1

    def test_multiple_highly_correlated_groups(self):
        """Test handling of multiple independent groups of correlated features."""
        np.random.seed(42)
        n_samples = 100

        # Group 1: feat_0 and feat_1 highly correlated
        base1 = np.random.randn(n_samples)
        feat_0 = base1 * 10.0
        feat_1 = base1 * 2.0  # Lower variance

        # Group 2: feat_2 and feat_3 highly correlated
        base2 = np.random.randn(n_samples)
        feat_2 = base2 * 5.0
        feat_3 = base2 * 1.0  # Lower variance

        # Unrelated feature
        feat_4 = np.random.randn(n_samples)

        X = np.column_stack([feat_0, feat_1, feat_2, feat_3, feat_4])
        feature_names = ["g1_high", "g1_low", "g2_high", "g2_low", "independent"]
        df = pd.DataFrame(X, columns=feature_names)

        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        # Should keep: g1_high, g2_high, independent (3 features)
        # Should drop: g1_low, g2_low (2 features)
        assert len(kept_features) == 3
        assert len(dropped_features) == 2
        assert "g1_high" in kept_features
        assert "g1_low" in dropped_features
        assert "g2_high" in kept_features
        assert "g2_low" in dropped_features
        assert "independent" in kept_features

    def test_variance_tie_breaker(self):
        """When variances are equal, the behavior should be deterministic (first encountered kept)."""
        np.random.seed(42)
        n_samples = 100
        base = np.random.randn(n_samples)

        # Two features with identical variance and high correlation
        feat_0 = base * 5.0 + np.random.randn(n_samples) * 0.1
        feat_1 = base * 5.0 + np.random.randn(n_samples) * 0.1

        X = np.column_stack([feat_0, feat_1])
        feature_names = ["feat_a", "feat_b"]
        df = pd.DataFrame(X, columns=feature_names)

        # Variances should be nearly identical
        var_a = df["feat_a"].var()
        var_b = df["feat_b"].var()
        assert abs(var_a - var_b) < 0.1, "Test setup: variances are too different"

        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        # One must be kept, one dropped
        assert len(kept_features) == 1
        assert len(dropped_features) == 1

    def test_threshold_boundary(self):
        """Features with correlation exactly at threshold should NOT be dropped."""
        np.random.seed(42)
        n_samples = 1000
        base = np.random.randn(n_samples)

        # Create correlation exactly at 0.95 (or very close)
        # feat_1 = 0.95 * feat_0 + noise
        feat_0 = base
        noise = np.random.randn(n_samples) * np.sqrt(1 - 0.95**2)
        feat_1 = 0.95 * feat_0 + noise

        X = np.column_stack([feat_0, feat_1])
        feature_names = ["feat_0", "feat_1"]
        df = pd.DataFrame(X, columns=feature_names)

        # Verify correlation is approximately 0.95
        corr = calculate_pearson_correlation(df["feat_0"], df["feat_1"])
        assert abs(corr - 0.95) < 0.01, f"Test setup failed: correlation {corr} is not ~0.95"

        # With threshold=0.95, correlation <= threshold should NOT be dropped
        # (The condition is typically > threshold)
        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        # Depending on implementation, this might keep both if strictly > 0.95
        # We expect both to be kept if the threshold check is strict
        assert len(kept_features) == 2
        assert len(dropped_features) == 0

    def test_three_mutually_correlated_features(self):
        """Test when three features are all highly correlated with each other."""
        np.random.seed(42)
        n_samples = 100
        base = np.random.randn(n_samples)

        # Three features all highly correlated with base
        feat_0 = base * 10.0
        feat_1 = base * 5.0
        feat_2 = base * 1.0

        X = np.column_stack([feat_0, feat_1, feat_2])
        feature_names = ["var_10", "var_5", "var_1"]
        df = pd.DataFrame(X, columns=feature_names)

        kept_features, dropped_features = check_collinearity(df, threshold=0.95)

        # Should keep only the highest variance feature
        assert len(kept_features) == 1
        assert kept_features[0] == "var_10"
        assert len(dropped_features) == 2
        assert set(dropped_features) == {"var_5", "var_1"}

    def test_empty_feature_set(self):
        """Edge case: empty dataframe should return empty lists."""
        df = pd.DataFrame()
        kept_features, dropped_features = check_collinearity(df, threshold=0.95)
        assert len(kept_features) == 0
        assert len(dropped_features) == 0

    def test_single_feature(self):
        """Edge case: single feature should be kept (no pairs to compare)."""
        np.random.seed(42)
        X = np.random.randn(100, 1)
        df = pd.DataFrame(X, columns=["single_feat"])

        kept_features, dropped_features = check_collinearity(df, threshold=0.95)
        assert len(kept_features) == 1
        assert kept_features[0] == "single_feat"
        assert len(dropped_features) == 0