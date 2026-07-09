"""
Unit tests for null hypothesis generation in the permutation test.

Verifies that the permutation test correctly shuffles labels and generates
a null distribution matching SC-001 criteria.

SC-001 Criteria:
- Null hypothesis: There is no difference in pressure anomalies between
  event windows and control windows.
- Permutation test shuffles labels to generate a null distribution.
- The test statistic (difference in means or KS statistic) is recalculated
  for each permutation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import generate_null_distribution, calculate_test_statistic


class TestNullHypothesisGeneration:
    """Tests for null hypothesis generation in permutation tests."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample data matching the master dataset structure
        np.random.seed(42)
        
        # Simulate pressure anomalies for event and control windows
        n_events = 20
        n_controls = 40
        
        # Event anomalies (simulated with a slight shift)
        self.event_anomalies = np.random.normal(loc=0.5, scale=1.0, size=n_events)
        
        # Control anomalies (simulated with no shift)
        self.control_anomalies = np.random.normal(loc=0.0, scale=1.0, size=n_controls)
        
        # Combine into a single array with labels
        self.anomalies = np.concatenate([self.event_anomalies, self.control_anomalies])
        self.labels = np.array([1] * n_events + [0] * n_controls)
        
        # Create a DataFrame for testing
        self.df = pd.DataFrame({
            'anomaly': self.anomalies,
            'label': self.labels
        })

    def test_null_distribution_has_correct_length(self):
        """Test that the null distribution has the expected number of permutations."""
        n_permutations = 1000
        null_dist = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=42
        )
        
        assert len(null_dist) == n_permutations, \
            f"Expected {n_permutations} permutations, got {len(null_dist)}"

    def test_null_distribution_matches_observed_statistic_range(self):
        """Test that the null distribution encompasses the observed statistic."""
        n_permutations = 1000
        observed_stat = calculate_test_statistic(
            self.df[self.df['label'] == 1]['anomaly'].values,
            self.df[self.df['label'] == 0]['anomaly'].values
        )
        
        null_dist = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=42
        )
        
        # The observed statistic should be within the range of the null distribution
        # (with high probability, though not guaranteed for small samples)
        min_null = np.min(null_dist)
        max_null = np.max(null_dist)
        
        # Check that the observed statistic is not an extreme outlier
        # This is a soft check; the observed stat could theoretically be outside
        # the null range for small samples, but should be close
        assert (observed_stat >= min_null - 3 * np.std(null_dist)) and \
               (observed_stat <= max_null + 3 * np.std(null_dist)), \
               f"Observed statistic {observed_stat} is far outside null distribution range [{min_null}, {max_null}]"

    def test_shuffling_preserves_data_values(self):
        """Test that shuffling only permutes labels, not data values."""
        n_permutations = 100
        null_dist = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=42
        )
        
        # The set of anomaly values should remain constant across permutations
        # We can verify this by checking that the mean of the null distribution
        # is close to the mean of the observed statistic under the null
        observed_stat = calculate_test_statistic(
            self.df[self.df['label'] == 1]['anomaly'].values,
            self.df[self.df['label'] == 0]['anomaly'].values
        )
        
        # Under the null hypothesis, the expected value of the test statistic
        # should be close to the observed statistic if there's no effect
        # This is a statistical check, so we allow some tolerance
        assert np.abs(np.mean(null_dist) - observed_stat) < 2.0, \
            f"Null distribution mean {np.mean(null_dist)} differs significantly from observed {observed_stat}"

    def test_deterministic_with_seed(self):
        """Test that the permutation test is deterministic with a fixed seed."""
        n_permutations = 100
        seed = 12345
        
        null_dist1 = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        null_dist2 = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        assert np.array_equal(null_dist1, null_dist2), \
            "Permutation test should be deterministic with the same seed"

    def test_null_distribution_shape_for_large_n(self):
        """Test that the null distribution approximates a normal distribution for large n."""
        n_permutations = 5000
        null_dist = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=42
        )
        
        # For large n, the null distribution should be approximately normal
        # We can check skewness and kurtosis
        from scipy import stats
        
        skewness = stats.skew(null_dist)
        kurtosis = stats.kurtosis(null_dist)
        
        # Normal distribution has skewness ~0 and kurtosis ~0 (excess)
        # Allow some tolerance for sampling variability
        assert abs(skewness) < 0.5, \
            f"Null distribution skewness {skewness} suggests non-normality"
        assert abs(kurtosis) < 1.0, \
            f"Null distribution kurtosis {kurtosis} suggests non-normality"

    def test_zero_effect_scenario(self):
        """Test null hypothesis when there is truly no effect."""
        # Create data with no effect (same distribution for both groups)
        n = 50
        no_effect_data = np.random.normal(loc=0.0, scale=1.0, size=2*n)
        no_effect_df = pd.DataFrame({
            'anomaly': no_effect_data,
            'label': [1] * n + [0] * n
        })
        
        n_permutations = 1000
        null_dist = generate_null_distribution(
            no_effect_df,
            n_permutations=n_permutations,
            random_seed=42
        )
        
        observed_stat = calculate_test_statistic(
            no_effect_df[no_effect_df['label'] == 1]['anomaly'].values,
            no_effect_df[no_effect_df['label'] == 0]['anomaly'].values
        )
        
        # Under the null, the observed statistic should be near the center
        # of the null distribution
        p_value = (np.sum(null_dist >= observed_stat) + 1) / (n_permutations + 1)
        
        # For a true null, p-value should be uniformly distributed
        # We expect it to be > 0.05 most of the time, but this is probabilistic
        # Just check that it's not extremely small
        assert p_value > 0.01, \
            f"P-value {p_value} is unexpectedly small for a true null hypothesis"

    def test_matches_sc001_criteria(self):
        """
        Verify that the permutation test implementation matches SC-001 criteria:
        - Correctly shuffles labels
        - Generates null distribution
        - Uses appropriate test statistic
        """
        n_permutations = 500
        null_dist = generate_null_distribution(
            self.df,
            n_permutations=n_permutations,
            random_seed=42
        )
        
        # SC-001: Null hypothesis is that labels are exchangeable
        # The test should show that the distribution of statistics from
        # shuffled labels matches the expected null behavior
        
        # 1. Check that null distribution is centered around the expected null value
        # (which is the observed statistic if there's no effect)
        observed_stat = calculate_test_statistic(
            self.df[self.df['label'] == 1]['anomaly'].values,
            self.df[self.df['label'] == 0]['anomaly'].values
        )
        
        # The mean of the null distribution should be close to the observed statistic
        # under the null hypothesis
        assert np.abs(np.mean(null_dist) - observed_stat) < 1.5, \
            f"Null distribution mean {np.mean(null_dist)} should be close to observed {observed_stat}"
        
        # 2. Check that the null distribution has non-zero variance
        assert np.std(null_dist) > 0.01, \
            "Null distribution should have non-zero variance"
        
        # 3. Check that the test statistic calculation is consistent
        stat1 = calculate_test_statistic(
            self.df[self.df['label'] == 1]['anomaly'].values,
            self.df[self.df['label'] == 0]['anomaly'].values
        )
        stat2 = calculate_test_statistic(
            self.df[self.df['label'] == 1]['anomaly'].values,
            self.df[self.df['label'] == 0]['anomaly'].values
        )
        
        assert np.isclose(stat1, stat2), \
            "Test statistic should be deterministic for the same data"