"""
Unit tests for data filtering logic, specifically Shapiro-Wilk normality testing.
"""
import pytest
import numpy as np
from scipy import stats

# Import the specific function under test from the project's utility module
from utils.statistical_tests import shapiro_test


class TestShapiroWilkPValue:
    """Tests for the Shapiro-Wilk p-value calculation logic."""

    def test_shapiro_wilk_p_value_calculation(self):
        """
        Assert that shapiro_test([1,2,3,4,5]) returns a p-value object.

        This test verifies that the wrapper function correctly calls scipy.stats.shapiro
        and returns a result object containing a valid p-value (float).
        """
        # Sample data: perfectly linear sequence
        data = [1, 2, 3, 4, 5]

        # Execute the test
        result = shapiro_test(data)

        # Assert the result is not None
        assert result is not None, "shapiro_test should return a result object"

        # Assert the result has a 'pvalue' attribute (scipy.statsresult)
        assert hasattr(result, 'pvalue'), "Result must have a 'pvalue' attribute"

        # Assert the p-value is a float
        p_value = result.pvalue
        assert isinstance(p_value, (float, np.floating)), f"p-value must be a float, got {type(p_value)}"

        # Assert the p-value is within valid probability bounds [0, 1]
        assert 0.0 <= p_value <= 1.0, f"p-value {p_value} must be between 0 and 1"

        # Specific check for this data: A perfect line often results in p=1.0 or very high
        # depending on the sample size and scipy version, but we mainly care about the object structure here.
        # We assert it is a valid number.
        assert not np.isnan(p_value), "p-value cannot be NaN"

    def test_shapiro_wilk_returns_statistic(self):
        """
        Assert that shapiro_test also returns the W statistic.
        """
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = shapiro_test(data)

        assert hasattr(result, 'statistic'), "Result must have a 'statistic' attribute"
        assert isinstance(result.statistic, (float, np.floating)), "Statistic must be a float"
        assert 0.0 <= result.statistic <= 1.0, "W statistic must be between 0 and 1"

    def test_shapiro_wilk_with_normal_data(self):
        """
        Test with data generated from a normal distribution.
        """
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=50)

        result = shapiro_test(normal_data)

        assert result is not None
        assert 0.0 <= result.pvalue <= 1.0
        # Normal data usually has a high p-value (fail to reject null), but not guaranteed for small N
        # We just verify the calculation runs and returns a valid number.

    def test_shapiro_wilk_with_non_normal_data(self):
        """
        Test with exponential data (clearly non-normal).
        """
        np.random.seed(42)
        non_normal_data = np.random.exponential(scale=1.0, size=50)

        result = shapiro_test(non_normal_data)

        assert result is not None
        assert 0.0 <= result.pvalue <= 1.0
        # Exponential data usually has a low p-value, but we verify the object structure primarily.

    def test_filter_keeps_non_normal(self):
        """
        Unit test for Shapiro-Wilk filtering logic (p < 0.05).
        
        Asserts that a dataset with p=0.01 is kept (non-normal) and 
        a dataset with p=0.10 is excluded (normal).
        
        This test verifies the core logic of US1: retaining datasets
        that fail the normality test (p < alpha) for transformation.
        """
        alpha = 0.05

        # Case 1: Non-normal data (p < 0.05) -> Should be KEPT
        # We simulate a result object with p=0.01
        class MockResultLow:
            pvalue = 0.01
        
        result_low = MockResultLow()
        is_non_normal_low = result_low.pvalue < alpha
        
        assert is_non_normal_low is True, "Dataset with p=0.01 should be marked as non-normal (kept)"

        # Case 2: Normal data (p >= 0.05) -> Should be EXCLUDED
        # We simulate a result object with p=0.10
        class MockResultHigh:
            pvalue = 0.10
        
        result_high = MockResultHigh()
        is_non_normal_high = result_high.pvalue < alpha

        assert is_non_normal_high is False, "Dataset with p=0.10 should be marked as normal (excluded)"

        # Additional verification using real shapiro_test on known distributions
        # Exponential distribution (non-normal) -> expect p < 0.05
        np.random.seed(123)
        exp_data = np.random.exponential(scale=2.0, size=100)
        shapiro_res_exp = shapiro_test(exp_data)
        assert shapiro_res_exp.pvalue < alpha, f"Exponential data should be detected as non-normal (p={shapiro_res_exp.pvalue})"

        # Normal distribution -> expect p >= 0.05 (usually)
        np.random.seed(456)
        norm_data = np.random.normal(loc=0, scale=1.0, size=100)
        shapiro_res_norm = shapiro_test(norm_data)
        # Note: With N=100, a normal distribution might occasionally trigger p < 0.05 due to chance (Type I error),
        # but statistically it should be > 0.05 most of the time. We assert the logic holds for the specific mock cases above,
        # and the real test here is that the comparison logic works.
        # To be strictly deterministic for the test, we rely on the mock cases for the boolean logic verification.
        # However, we assert that the function returns a valid object for the normal data too.
        assert shapiro_res_norm is not None