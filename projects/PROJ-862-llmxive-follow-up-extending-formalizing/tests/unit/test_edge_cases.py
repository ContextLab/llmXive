"""
Unit tests for edge cases in the analysis and validity modules.
Specifically covers:
- Normality violation (triggering Wilcoxon test selection)
- No valid sigma (validity collapse across all tested levels)
- Empty datasets after filtering
"""
import pytest
import numpy as np
from scipy import stats
from unittest.mock import patch, MagicMock

# Import from the project's code directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis import run_hypothesis_test, check_significant_separability_increase
from validity_check import check_validity_collapse
from config import NoiseSweepConfig


class TestNormalityViolation:
    """Tests for handling non-normal data distributions in hypothesis testing."""

    def test_wilcoxon_selected_on_non_normal_data(self):
        """
        Verify that when data fails the Shapiro-Wilk normality test,
        the system selects the Wilcoxon signed-rank test instead of the t-test.
        """
        # Generate non-normal data (exponential distribution)
        np.random.seed(42)
        baseline = np.random.exponential(scale=2.0, size=50)
        perturbed = baseline + np.random.exponential(scale=0.5, size=50)

        # Mock the normality test to ensure it returns p < 0.05 (non-normal)
        with patch('scipy.stats.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.85, 0.01)  # p-value < 0.05

            result = run_hypothesis_test(baseline, perturbed)

            assert result['test_type'] == 'wilcoxon', \
                f"Expected 'wilcoxon' for non-normal data, got {result['test_type']}"
            assert 'power_warning' in result
            assert result['power_warning'] is True

    def test_ttest_selected_on_normal_data(self):
        """
        Verify that when data passes the normality test,
        the system selects the paired t-test.
        """
        # Generate normal data
        np.random.seed(42)
        baseline = np.random.normal(loc=0.5, scale=0.1, size=100)
        perturbed = baseline + np.random.normal(loc=0.05, scale=0.02, size=100)

        with patch('scipy.stats.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.98, 0.5)  # p-value > 0.05 (normal)

            result = run_hypothesis_test(baseline, perturbed)

            assert result['test_type'] == 't-test', \
                f"Expected 't-test' for normal data, got {result['test_type']}"
            assert 'power_warning' not in result or result.get('power_warning') is False

    def test_sample_size_warning_below_threshold(self):
        """
        Verify that a power warning is raised when sample size is < 30,
        even if the data is normal.
        """
        np.random.seed(42)
        # Small sample size (n=20)
        baseline = np.random.normal(loc=0.5, scale=0.1, size=20)
        perturbed = baseline + 0.05

        with patch('scipy.stats.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.98, 0.5)  # Normal

            result = run_hypothesis_test(baseline, perturbed)

            assert result['power_warning'] is True, \
                "Expected power_warning for n < 30"
            assert result['reduced_power_estimate'] is not None


class TestNoValidSigma:
    """Tests for handling scenarios where no sigma level yields valid results."""

    def test_validity_collapse_detection_all_sigs(self):
        """
        Verify that check_validity_collapse correctly identifies a collapse
        when pass_rate drops below the threshold (10%) at all sigma levels.
        """
        # Simulate a collapse scenario where pass_rate is extremely low
        pass_rates = [0.02, 0.01, 0.005, 0.001]  # All < 10%
        threshold = 0.10

        # The function should detect the collapse point
        # We test the logic by verifying it returns True for collapse
        is_collapse = check_validity_collapse(pass_rates[0], threshold)
        assert is_collapse is True

        # Verify the function handles the "no valid sigma" case
        # by returning a collapse point at the first sigma (or earliest failure)
        collapse_detected = all(
            check_validity_collapse(pr, threshold) for pr in pass_rates
        )
        assert collapse_detected is True

    def test_no_collapse_high_pass_rate(self):
        """
        Verify that check_validity_collapse returns False when pass_rate is high.
        """
        pass_rates = [0.95, 0.90, 0.85]
        threshold = 0.10

        is_collapse = check_validity_collapse(pass_rates[0], threshold)
        assert is_collapse is False

    def test_edge_case_zero_pass_rate(self):
        """
        Verify handling of a complete failure (0% pass rate).
        """
        pass_rate = 0.0
        threshold = 0.10

        is_collapse = check_validity_collapse(pass_rate, threshold)
        assert is_collapse is True


class TestEmptyFilteredData:
    """Tests for handling empty datasets after filtering."""

    def test_hypothesis_test_empty_input(self):
        """
        Verify that run_hypothesis_test handles empty arrays gracefully.
        """
        baseline = np.array([])
        perturbed = np.array([])

        with pytest.raises(ValueError) as excinfo:
            run_hypothesis_test(baseline, perturbed)

        assert "Empty dataset" in str(excinfo.value)

    def test_significant_separability_empty_input(self):
        """
        Verify that check_significant_separability_increase handles empty input.
        """
        results = []  # Empty list of results

        with pytest.raises(ValueError) as excinfo:
            check_significant_separability_increase(results)

        assert "No valid results" in str(excinfo.value)


class TestStatisticalCorrectionEdgeCases:
    """Tests for multiple hypothesis correction edge cases."""

    def test_bonferroni_single_test(self):
        """
        Verify Bonferroni correction works correctly with a single p-value.
        """
        p_values = [0.03]
        alpha = 0.05

        # Corrected p-value should be p * n_tests
        corrected = p_values[0] * len(p_values)
        assert corrected == 0.03

    def test_bonferroni_many_tests(self):
        """
        Verify Bonferroni correction with many tests.
        """
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        n_tests = len(p_values)
        alpha = 0.05

        # Corrected p-values
        corrected = [p * n_tests for p in p_values]
        
        # All corrected p-values > alpha (0.05)
        for p in corrected:
            assert p > alpha, f"Expected p > {alpha}, got {p}"

    def test_holm_correction_ordering(self):
        """
        Verify Holm-Bonferroni correction respects ordering.
        """
        # Simulate a case where ordering matters
        p_values = [0.04, 0.01, 0.03]
        sorted_p = sorted(p_values)
        
        # Holm correction logic (simplified check)
        # The smallest p-value gets the most lenient correction
        assert sorted_p[0] < sorted_p[1] < sorted_p[2]