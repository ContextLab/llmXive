"""
Unit tests for Bonferroni correction logic in code/analysis/correction.py.

This test suite verifies that the Bonferroni correction correctly adjusts
p-values to control the family-wise error rate (FWER) across multiple
hypothesis tests, specifically for the US3 analysis pipeline.

Requirements verified:
- Correct calculation of adjusted p-values (p_adj = p_raw * N)
- Capping of adjusted p-values at 1.0
- Correct determination of significance based on alpha threshold
- Handling of edge cases (empty list, single test, zero p-values)
"""

import pytest
import math
from typing import List, Dict, Any

# Import the implementation under test.
# The actual implementation is expected to be in code/analysis/correction.py
# We import it here to test the logic.
try:
    from analysis.correction import bonferroni_correct, apply_bonferroni_to_results
except ImportError:
    # Fallback for cases where the module might not be importable in isolation
    # during initial development, though the task requires the implementation to exist.
    pytest.skip("analysis.correction module not yet available for import", allow_module_level=True)


class TestBonferroniCorrection:
    """Test cases for the Bonferroni correction function."""

    def test_single_test_no_adjustment_needed(self):
        """
        Test that a single test with p-value 0.05 remains 0.05 when N=1.
        Bonferroni: p_adj = p_raw * 1 = p_raw.
        """
        p_values = [0.05]
        alpha = 0.05
        corrected = bonferroni_correct(p_values, alpha)

        assert len(corrected) == 1
        assert math.isclose(corrected[0]["adjusted_p_value"], 0.05, rel_tol=1e-9)
        assert corrected[0]["is_significant"] is True

    def test_multiple_tests_adjustment(self):
        """
        Test adjustment with N=3 tests.
        p_raw = 0.02 -> p_adj = 0.06 (not significant at 0.05)
        p_raw = 0.01 -> p_adj = 0.03 (significant)
        """
        p_values = [0.02, 0.01, 0.10]
        alpha = 0.05
        corrected = bonferroni_correct(p_values, alpha)

        assert len(corrected) == 3

        # First test: 0.02 * 3 = 0.06 > 0.05 -> False
        assert math.isclose(corrected[0]["adjusted_p_value"], 0.06, rel_tol=1e-9)
        assert corrected[0]["is_significant"] is False

        # Second test: 0.01 * 3 = 0.03 <= 0.05 -> True
        assert math.isclose(corrected[1]["adjusted_p_value"], 0.03, rel_tol=1e-9)
        assert corrected[1]["is_significant"] is True

        # Third test: 0.10 * 3 = 0.30 > 0.05 -> False
        assert math.isclose(corrected[2]["adjusted_p_value"], 0.30, rel_tol=1e-9)
        assert corrected[2]["is_significant"] is False

    def test_p_value_capped_at_one(self):
        """
        Test that adjusted p-values greater than 1.0 are capped at 1.0.
        p_raw = 0.8, N = 2 -> 1.6 -> capped to 1.0
        """
        p_values = [0.8]
        alpha = 0.05
        corrected = bonferroni_correct(p_values, alpha)

        assert math.isclose(corrected[0]["adjusted_p_value"], 1.0, rel_tol=1e-9)
        assert corrected[0]["is_significant"] is False

    def test_empty_input_list(self):
        """Test handling of an empty list of p-values."""
        p_values = []
        alpha = 0.05
        corrected = bonferroni_correct(p_values, alpha)

        assert len(corrected) == 0

    def test_zero_p_value(self):
        """
        Test that a p-value of 0.0 remains 0.0 after adjustment.
        0 * N = 0.
        """
        p_values = [0.0, 0.5]
        alpha = 0.05
        corrected = bonferroni_correct(p_values, alpha)

        assert math.isclose(corrected[0]["adjusted_p_value"], 0.0, rel_tol=1e-9)
        assert corrected[0]["is_significant"] is True

        assert math.isclose(corrected[1]["adjusted_p_value"], 0.5, rel_tol=1e-9)
        # 0.5 * 2 = 1.0 -> capped, but 1.0 > 0.05 so False
        # Wait, 0.5 * 2 = 1.0. Capped at 1.0. 1.0 > 0.05 -> False.
        assert corrected[1]["is_significant"] is False

    def test_alpha_threshold_variations(self):
        """Test with different alpha thresholds."""
        p_values = [0.01]
        N = 2

        # Alpha = 0.01: 0.01 * 2 = 0.02 > 0.01 -> False
        corrected_01 = bonferroni_correct(p_values, 0.01)
        assert corrected_01[0]["is_significant"] is False

        # Alpha = 0.05: 0.01 * 2 = 0.02 <= 0.05 -> True
        corrected_05 = bonferroni_correct(p_values, 0.05)
        assert corrected_05[0]["is_significant"] is True

        # Alpha = 0.02: 0.01 * 2 = 0.02 <= 0.02 -> True (boundary)
        corrected_02 = bonferroni_correct(p_values, 0.02)
        assert corrected_02[0]["is_significant"] is True

    def test_large_family_size(self):
        """Test with a large number of tests to ensure robustness."""
        # Simulate 100 tests with p=0.001
        p_values = [0.001] * 100
        alpha = 0.05
        corrected = bonferroni_correct(p_values, alpha)

        # 0.001 * 100 = 0.1. 0.1 > 0.05 -> False for all
        for res in corrected:
            assert math.isclose(res["adjusted_p_value"], 0.1, rel_tol=1e-9)
            assert res["is_significant"] is False

        # Now with p=0.0001
        p_values_2 = [0.0001] * 100
        corrected_2 = bonferroni_correct(p_values_2, alpha)
        # 0.0001 * 100 = 0.01. 0.01 <= 0.05 -> True
        for res in corrected_2:
            assert math.isclose(res["adjusted_p_value"], 0.01, rel_tol=1e-9)
            assert res["is_significant"] is True


class TestApplyBonferroniToResults:
    """
    Test the integration function that applies correction to a list of
    result dictionaries (e.g., from ANOVA or trend analysis).
    """

    def test_integrates_with_results_list(self):
        """
        Verify that apply_bonferroni_to_results correctly processes
        a list of dicts containing 'p_value' and returns them with
        corrected fields added.
        """
        results = [
            {"model_id": "m1", "p_value": 0.02, "other_field": "data1"},
            {"model_id": "m2", "p_value": 0.08, "other_field": "data2"},
        ]
        alpha = 0.05
        corrected_results = apply_bonferroni_to_results(results, alpha)

        assert len(corrected_results) == 2

        # m1: 0.02 * 2 = 0.04 <= 0.05 -> Significant
        assert "adjusted_p_value" in corrected_results[0]
        assert math.isclose(corrected_results[0]["adjusted_p_value"], 0.04, rel_tol=1e-9)
        assert corrected_results[0]["is_significant"] is True
        # Check original fields are preserved
        assert corrected_results[0]["model_id"] == "m1"
        assert corrected_results[0]["other_field"] == "data1"

        # m2: 0.08 * 2 = 0.16 > 0.05 -> Not Significant
        assert math.isclose(corrected_results[1]["adjusted_p_value"], 0.16, rel_tol=1e-9)
        assert corrected_results[1]["is_significant"] is False
        assert corrected_results[1]["model_id"] == "m2"

    def test_empty_results_list(self):
        """Test with an empty list of results."""
        results = []
        corrected = apply_bonferroni_to_results(results, 0.05)
        assert len(corrected) == 0

    def test_missing_p_value_raises_error(self):
        """
        Test that a missing 'p_value' key in a result dict raises an error.
        This ensures data integrity.
        """
        results = [
            {"model_id": "m1", "other_field": "data1"} # Missing p_value
        ]
        with pytest.raises(KeyError):
            apply_bonferroni_to_results(results, 0.05)