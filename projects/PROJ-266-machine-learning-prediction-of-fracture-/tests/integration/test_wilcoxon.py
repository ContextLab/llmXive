"""
Integration test for Wilcoxon signed-rank test logic.
Verifies that the statistical comparison between CNN and baseline models
works correctly with mock distributions of MAE scores.
"""
import pytest
import numpy as np
from scipy import stats

# Import the function to be tested.
# We expect this to exist in code/train/stats.py based on the task description T025a.
# If the file doesn't exist yet, this test will fail to import, which is the correct behavior
# (fail loudly) to indicate the prerequisite task T025a is incomplete.
try:
    from code.train.stats import wilcoxon_test
except ImportError:
    pytest.fail("code.train.stats.wilcoxon_test not found. Prerequisite task T025a may be incomplete.")


class TestWilcoxonIntegration:
    def test_wilcoxon_significant_difference(self):
        """
        Test case where there is a clear difference between two distributions.
        CNN should have significantly lower MAE than a random baseline.
        """
        # Simulate MAE distributions from multiple seeds
        # CNN: consistently low error
        cnn_mae = np.array([0.10, 0.12, 0.09, 0.11, 0.10])
        # Baseline: consistently high error
        baseline_mae = np.array([0.50, 0.55, 0.48, 0.52, 0.51])

        p_value, statistic = wilcoxon_test(cnn_mae, baseline_mae)

        assert isinstance(p_value, float), "p_value must be a float"
        assert isinstance(statistic, (int, float)), "statistic must be a number"
        assert p_value < 0.05, "Expected significant difference (p < 0.05)"

    def test_wilcoxon_no_significant_difference(self):
        """
        Test case where two distributions are identical.
        p-value should be high (not significant).
        """
        # Identical distributions
        model_a = np.array([0.20, 0.21, 0.19, 0.20, 0.21])
        model_b = np.array([0.20, 0.21, 0.19, 0.20, 0.21])

        p_value, statistic = wilcoxon_test(model_a, model_b)

        assert isinstance(p_value, float), "p_value must be a float"
        assert p_value >= 0.05, "Expected no significant difference (p >= 0.05)"

    def test_wilcoxon_different_sizes_error(self):
        """
        Test that the function raises an error if input arrays have different lengths.
        Wilcoxon signed-rank test requires paired samples.
        """
        model_a = np.array([0.20, 0.21, 0.19])
        model_b = np.array([0.20, 0.21, 0.19, 0.20])

        with pytest.raises(ValueError):
            wilcoxon_test(model_a, model_b)

    def test_wilcoxon_single_seed(self):
        """
        Test with only one seed (edge case).
        """
        model_a = np.array([0.20])
        model_b = np.array([0.25])

        p_value, statistic = wilcoxon_test(model_a, model_b)
        
        # With n=1, scipy usually returns p=1.0 or handles it gracefully.
        # We just verify it doesn't crash and returns a float.
        assert isinstance(p_value, float)

    def test_wilcoxon_integration_with_realistic_data(self):
        """
        Integration test using more realistic, slightly noisy distributions
        to ensure the statistical test behaves as expected in a realistic scenario.
        """
        np.random.seed(42)
        # CNN with mean 0.15, std 0.02
        cnn_scores = np.random.normal(0.15, 0.02, 10)
        # Baseline with mean 0.25, std 0.03
        baseline_scores = np.random.normal(0.25, 0.03, 10)

        p_value, statistic = wilcoxon_test(cnn_scores, baseline_scores)

        assert p_value < 0.05, "With these distributions, we expect a significant difference"
        assert statistic > 0, "Statistic should be positive if cnn_scores are generally lower"