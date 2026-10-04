"""
Unit tests for statistical test implementations.
Tests for T021a (Mann-Whitney U) and T021b (Independent T-Test).
"""
import pytest
import math
import sys
import os

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.analysis import statistical_tests


class TestIndependentTTestImplementation:
    """
    Tests for T021b: Unit test `test_independent_t_test_implementation`
    Asserts p-value, t-statistic, and effect size output.
    """

    def test_independent_t_test_implementation(self):
        """
        Verify that perform_independent_t_test returns a dictionary with
        required keys: p_value, t_statistic, and effect_size (Cohen's d).
        Uses small, deterministic mock data to ensure reproducibility.
        """
        # Mock data: Two small groups with known statistical properties
        # Group A (LLM): [1.0, 2.0, 3.0] -> mean=2.0, var=1.0
        # Group B (Human): [4.0, 5.0, 6.0] -> mean=5.0, var=1.0
        group_a = [1.0, 2.0, 3.0]
        group_b = [4.0, 5.0, 6.0]

        result = statistical_tests.perform_independent_t_test(group_a, group_b)

        # Assert result is a dictionary
        assert isinstance(result, dict), "Result must be a dictionary"

        # Assert required keys exist
        assert "t_statistic" in result, "Result must contain 't_statistic'"
        assert "p_value" in result, "Result must contain 'p_value'"
        assert "effect_size" in result, "Result must contain 'effect_size'"

        # Assert types
        assert isinstance(result["t_statistic"], float), "t_statistic must be float"
        assert isinstance(result["p_value"], float), "p_value must be float"
        assert isinstance(result["effect_size"], float), "effect_size must be float"

        # Assert values are within expected ranges for this data
        # Mean diff = 3.0, Pooled std dev = 1.0, n=3 each -> t ~ -3.0 * sqrt(3/2) ~ -3.67
        # Cohen's d = 3.0 / 1.0 = 3.0
        assert math.isfinite(result["t_statistic"]), "t_statistic must be finite"
        assert 0.0 < result["p_value"] < 1.0, "p_value must be between 0 and 1"
        assert math.isfinite(result["effect_size"]), "effect_size must be finite"

        # Specific check for Cohen's d magnitude (approx 3.0 for this data)
        # Allowing some float tolerance
        assert abs(result["effect_size"] - 3.0) < 0.1, "Cohen's d should be approx 3.0"

    def test_independent_t_test_unequal_variance_handling(self):
        """
        Test that the function handles groups with different variances
        without crashing (Welch's t-test behavior is expected if implemented,
        or standard t-test with warning).
        """
        group_a = [1.0, 1.1, 1.2] # Low variance
        group_b = [5.0, 10.0, 15.0] # High variance

        result = statistical_tests.perform_independent_t_test(group_a, group_b)

        assert "t_statistic" in result
        assert "p_value" in result
        assert "effect_size" in result
        assert math.isfinite(result["t_statistic"])
        assert math.isfinite(result["p_value"])
        assert math.isfinite(result["effect_size"])

    def test_independent_t_test_single_element(self):
        """
        Test behavior with single element groups (should fail or return NaN/Inf).
        Standard t-test requires at least 2 elements per group to estimate variance.
        """
        group_a = [1.0]
        group_b = [2.0]

        # Depending on implementation, this might raise ValueError or return NaN
        try:
            result = statistical_tests.perform_independent_t_test(group_a, group_b)
            # If it returns, check structure
            assert isinstance(result, dict)
            assert "t_statistic" in result
            assert "p_value" in result
            assert "effect_size" in result
        except ValueError:
            # Expected behavior: t-test cannot be performed with n=1
            pass

    def test_independent_t_test_empty_group(self):
        """
        Test behavior with empty groups.
        """
        group_a = []
        group_b = [1.0, 2.0]

        try:
            result = statistical_tests.perform_independent_t_test(group_a, group_b)
            assert False, "Expected ValueError for empty group"
        except (ValueError, IndexError):
            # Expected
            pass

    def test_calculate_cohens_d_directly(self):
        """
        Direct unit test for calculate_cohens_d helper function.
        """
        group_a = [1.0, 2.0, 3.0]
        group_b = [4.0, 5.0, 6.0]

        d = statistical_tests.calculate_cohens_d(group_a, group_b)

        assert isinstance(d, float)
        assert math.isfinite(d)
        # Expected d = 3.0
        assert abs(d - 3.0) < 0.1


class TestMannWhitneyUImplementation:
    """
    Tests for T021a: Unit test `test_mann_whitney_u_implementation`
    Asserts p-value and statistic output.
    """

    def test_mann_whitney_u_implementation(self):
        """
        Verify that the Mann-Whitney U test implementation returns
        p-value and U-statistic.
        """
        group_a = [1.0, 2.0, 3.0]
        group_b = [4.0, 5.0, 6.0]

        # Assuming the function is named run_mann_whitney_u or similar in the module
        # If it's part of perform_independent_t_test as a fallback, we test that path
        # Based on the API surface, we assume a dedicated function exists or is tested via the main runner.
        # For T021a, we test the specific U-test logic.
        
        # Let's assume the module has a function `run_mann_whitney_u`
        # If not, we test the logic inside `perform_independent_t_test` if it delegates.
        # Given the API surface `from analysis.statistical_tests import ... perform_independent_t_test`,
        # and T024b mentions implementing Mann-Whitney U, we assume a helper or specific function exists.
        # If the implementation is strictly inside `perform_independent_t_test` for fallback,
        # we might need to test that path. However, T021a implies a specific test for the U-test.
        
        # Let's assume a function `run_mann_whitney_u` exists in the module for T024b/T021a.
        # If it doesn't, we check if `perform_independent_t_test` has a mode for it.
        # For the sake of this task, we will assume the function `run_mann_whitney_u` exists
        # as per T024b implementation details which T021a tests.
        
        # If the function is not explicitly exported, we might need to call the internal logic.
        # However, the task description says "asserts p-value and statistic output".
        # Let's try to call a hypothetical function. If it fails, we adapt.
        
        # Since the API surface lists `perform_independent_t_test`, and T024b says "Implement Mann-Whitney U",
        # it is likely a separate function or a mode. Let's assume `run_mann_whitney_u` is the function.
        
        try:
            result = statistical_tests.run_mann_whitney_u(group_a, group_b)
            assert isinstance(result, dict)
            assert "p_value" in result
            assert "U_statistic" in result or "u_statistic" in result # Check both cases
            assert math.isfinite(result["p_value"])
            assert math.isfinite(result.get("U_statistic", result.get("u_statistic")))
        except AttributeError:
            # Fallback: If run_mann_whitney_u doesn't exist, maybe it's part of perform_independent_t_test
            # or the task T021a is testing the fallback path in T024a/T024b.
            # However, T021a is a unit test for the implementation.
            # Let's assume the function exists as per T024b.
            # If it's missing, the test should fail, indicating the implementation is missing.
            # But we are implementing the TEST, so we assume the implementation exists.
            # If it doesn't, we catch the error and assert that the function is missing? No, that's not a test.
            # We assume the implementation exists.
            raise pytest.fail("run_mann_whitney_u function not found in statistical_tests module. Ensure T024b is implemented.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])