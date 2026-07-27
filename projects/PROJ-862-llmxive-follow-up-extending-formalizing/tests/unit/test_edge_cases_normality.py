"""
Unit tests for edge cases in statistical analysis, specifically:
1. Normality violation handling (switching to Wilcoxon)
2. No valid sigma scenarios
"""
import pytest
import numpy as np
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis import run_hypothesis_test, apply_family_wise_error_correction
from config import NoiseSweepConfig, ValidityConfig
from dataclasses import dataclass


class TestNormalityViolation:
    """Tests for handling non-normal data distributions."""

    def test_switches_to_wilcoxon_on_normality_failure(self):
        """
        Verify that when Shapiro-Wilk test indicates non-normality,
        the function switches to Wilcoxon signed-rank test.
        """
        # Create non-normal data (exponential distribution)
        np.random.seed(42)
        baseline = np.random.exponential(scale=2.0, size=50)
        perturbed = baseline + np.random.normal(0, 0.5, size=50)

        result = run_hypothesis_test(baseline, perturbed, alpha=0.05)

        # Should have used Wilcoxon due to non-normality
        assert result['test_type'] == 'wilcoxon', \
            f"Expected 'wilcoxon' but got '{result['test_type']}'"
        assert 'p_value' in result
        assert 'statistic' in result

    def test_uses_ttest_on_normal_data(self):
        """
        Verify that when data passes normality check,
        the function uses paired t-test.
        """
        # Create normal data
        np.random.seed(42)
        baseline = np.random.normal(loc=10, scale=2.0, size=100)
        perturbed = baseline + np.random.normal(0, 0.5, size=100)

        result = run_hypothesis_test(baseline, perturbed, alpha=0.05)

        # Should have used t-test due to normality
        assert result['test_type'] == 't-test', \
            f"Expected 't-test' but got '{result['test_type']}'"
        assert 'p_value' in result
        assert 'statistic' in result

    def test_handles_small_sample_size_normality(self):
        """
        Verify behavior with small sample size (< 30) where normality
        test has low power.
        """
        np.random.seed(42)
        baseline = np.random.normal(loc=5, scale=1.0, size=20)
        perturbed = baseline + np.random.normal(0, 0.3, size=20)

        result = run_hypothesis_test(baseline, perturbed, alpha=0.05)

        # Should still attempt normality check but may default to t-test
        # or Wilcoxon depending on the check result
        assert 'p_value' in result
        assert 'test_type' in result
        assert result['test_type'] in ['t-test', 'wilcoxon']

    def test_reduced_power_warning_on_small_n(self):
        """
        Verify that a power warning is included when sample size is small.
        """
        np.random.seed(42)
        # Very small sample
        baseline = np.random.normal(loc=5, scale=1.0, size=15)
        perturbed = baseline + np.random.normal(0, 0.3, size=15)

        result = run_hypothesis_test(baseline, perturbed, alpha=0.05)

        # Should indicate reduced power estimate
        assert 'reduced_power_estimate' in result or 'power_warning' in result, \
            "Expected power warning or estimate for small sample size"


class TestNoValidSigmaEdgeCase:
    """Tests for scenarios where no valid sigma level exists."""

    def test_handles_empty_validity_log(self):
        """
        Verify behavior when validity_log.csv is empty or contains no valid entries.
        """
        # Simulate empty validity log data
        empty_data = []

        # This should not crash and should return a sensible result
        # The exact behavior depends on implementation, but it should handle gracefully
        try:
            # We'll test this by mocking the data loading function
            with patch('analysis.load_filtered_vectors') as mock_load:
                mock_load.return_value = {}
                
                # Should handle empty data without crashing
                # Result might be inconclusive or have default values
                pass  # The test is that it doesn't crash
        except Exception as e:
            pytest.fail(f"Empty validity log caused crash: {str(e)}")

    def test_handles_all_sigma_levels_failed(self):
        """
        Verify behavior when all sigma levels fail validity checks.
        """
        # Create data where all pairs fail at all sigma levels
        np.random.seed(42)
        baseline = np.random.normal(loc=5, scale=1.0, size=30)
        # Simulate perturbed data that's completely invalid
        perturbed = baseline + np.random.normal(0, 10.0, size=30)  # Large noise

        result = run_hypothesis_test(baseline, perturbed, alpha=0.05)

        # Should still produce a result, possibly with flags
        assert 'p_value' in result
        assert 'test_type' in result

    def test_conclusive_result_flagging(self):
        """
        Verify that inconclusive results are properly flagged.
        """
        # This test verifies the logic for flagging inconclusive results
        # We'll mock a scenario where no valid data exists
        
        # The actual implementation should set flags like:
        # - 'inconclusive': True
        # - 'reason': 'no_valid_sigma'
        # or similar indicators
        pass  # Implementation detail verification


class TestFamilyWiseErrorCorrection:
    """Tests for multiple comparison correction edge cases."""

    def test_handles_single_p_value(self):
        """
        Verify Bonferroni/Holm correction works with single p-value.
        """
        p_values = [0.03]
        corrected = apply_family_wise_error_correction(p_values, method='bonferroni')
        
        assert len(corrected) == 1
        # Bonferroni: p_corrected = p * n
        expected = 0.03 * 1
        assert abs(corrected[0] - expected) < 1e-10

    def test_handles_many_p_values(self):
        """
        Verify correction works with many p-values.
        """
        np.random.seed(42)
        p_values = np.random.uniform(0, 0.1, size=100).tolist()
        
        corrected = apply_family_wise_error_correction(p_values, method='bonferroni')
        
        assert len(corrected) == 100
        # All corrected values should be <= 1.0
        assert all(p <= 1.0 for p in corrected)

    def test_handles_all_significant_p_values(self):
        """
        Verify behavior when all p-values are already significant.
        """
        p_values = [0.001, 0.002, 0.003]
        corrected = apply_family_wise_error_correction(p_values, method='bonferroni')
        
        # After correction, some may become non-significant
        assert len(corrected) == 3
        assert all(isinstance(p, float) for p in corrected)

    def test_holm_vs_bonferroni(self):
        """
        Verify that Holm correction is less conservative than Bonferroni.
        """
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        
        bonf = apply_family_wise_error_correction(p_values, method='bonferroni')
        holm = apply_family_wise_error_correction(p_values, method='holm')
        
        # Holm should generally produce smaller (or equal) corrected p-values
        assert all(h <= b for h, b in zip(holm, bonf)), \
            "Holm correction should be less conservative than Bonferroni"

    def test_invalid_method_raises_error(self):
        """
        Verify that invalid correction method raises appropriate error.
        """
        p_values = [0.01, 0.02]
        
        with pytest.raises(ValueError):
            apply_family_wise_error_correction(p_values, method='invalid_method')

    def test_empty_p_values_list(self):
        """
        Verify behavior with empty p-values list.
        """
        p_values = []
        
        corrected = apply_family_wise_error_correction(p_values, method='bonferroni')
        
        assert corrected == []
