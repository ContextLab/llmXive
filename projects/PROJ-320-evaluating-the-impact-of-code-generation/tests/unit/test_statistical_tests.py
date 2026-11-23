"""Unit tests for statistical tests implementation (US2)."""
import math
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from code.analysis import statistical_tests


class TestMannWhitneyU:
    """Tests for Mann-Whitney U test implementation."""

    def test_mann_whitney_u_implementation(self):
        """Test Mann-Whitney U test with known mock data.
        
        Input: {'llm': [1, 2, 3], 'human': [4, 5, 6]}
        Expected: p_value approx 0.1, U_statistic approx 0.0
        
        The Mann-Whitney U test compares two independent samples.
        For the given data:
        - llm values: 1, 2, 3 (all lower than human values)
        - human values: 4, 5, 6 (all higher than llm values)
        
        When all values in one group are strictly less than all values 
        in the other group, U_statistic should be 0.
        
        The p-value for n1=3, n2=3 with U=0 is approximately 0.1 (exact: 0.1).
        """
        llm_data = [1, 2, 3]
        human_data = [4, 5, 6]
        
        result = statistical_tests.mann_whitney_u_test(llm_data, human_data)
        
        # Check that result contains required keys
        assert "p_value" in result, "Result must contain p_value"
        assert "U_statistic" in result, "Result must contain U_statistic"
        
        # Check U_statistic is approximately 0.0
        # For the given data, all llm < all human, so U should be 0
        assert math.isclose(result["U_statistic"], 0.0, abs_tol=0.01), \
            f"Expected U_statistic ≈ 0.0, got {result['U_statistic']}"
        
        # Check p_value is approximately 0.1
        # For n1=3, n2=3, U=0, the two-tailed p-value is 0.1
        assert math.isclose(result["p_value"], 0.1, abs_tol=0.01), \
            f"Expected p_value ≈ 0.1, got {result['p_value']}"

    def test_mann_whitney_u_identical_distributions(self):
        """Test with identical distributions - should have high p-value."""
        llm_data = [1, 2, 3, 4, 5]
        human_data = [1, 2, 3, 4, 5]
        
        result = statistical_tests.mann_whitney_u_test(llm_data, human_data)
        
        assert result["p_value"] > 0.05, \
            f"Identical distributions should have p > 0.05, got {result['p_value']}"
        assert result["U_statistic"] >= 0, \
            f"U statistic should be non-negative, got {result['U_statistic']}"

    def test_mann_whitney_u_single_element(self):
        """Test with single element in each group."""
        llm_data = [5]
        human_data = [10]
        
        result = statistical_tests.mann_whitney_u_test(llm_data, human_data)
        
        assert "p_value" in result
        assert "U_statistic" in result
        # For n1=1, n2=1, U=0, p-value = 1.0 (two-tailed)
        assert result["p_value"] == 1.0, \
            f"Expected p_value = 1.0 for n1=n2=1, got {result['p_value']}"

    def test_mann_whitney_u_large_sample(self):
        """Test with larger samples to ensure scalability."""
        llm_data = list(range(1, 51))
        human_data = list(range(51, 101))
        
        result = statistical_tests.mann_whitney_u_test(llm_data, human_data)
        
        assert result["p_value"] < 0.001, \
            f"Large separation should yield very small p-value, got {result['p_value']}"
        assert result["U_statistic"] == 0.0, \
            f"U should be 0 when all llm < all human, got {result['U_statistic']}"


class TestIndependentTTest:
    """Tests for independent t-test implementation."""

    def test_independent_t_test_implementation(self):
        """Test independent t-test with known mock data.
        
        Input: {'llm': [1, 2, 3], 'human': [4, 5, 6]}
        Expected: p_value approx 0.05, t_statistic approx -2.0, effect_size approx 1.5
        
        For the given data:
        - llm mean = 2.0, std = 1.0
        - human mean = 5.0, std = 1.0
        - Difference in means = -3.0
        
        The t-statistic should be approximately -2.0 to -2.5 depending on 
        whether equal variance is assumed.
        """
        llm_data = [1, 2, 3]
        human_data = [4, 5, 6]
        
        result = statistical_tests.t_test(llm_data, human_data)
        
        # Check that result contains required keys
        assert "p_value" in result, "Result must contain p_value"
        assert "t_statistic" in result, "Result must contain t_statistic"
        assert "effect_size" in result, "Result must contain effect_size"
        
        # Check t_statistic is approximately -2.0 (within reasonable range)
        # For equal variance t-test with these values, t ≈ -2.0
        assert -3.0 <= result["t_statistic"] <= -1.0, \
            f"Expected t_statistic between -3.0 and -1.0, got {result['t_statistic']}"
        
        # Check p_value is approximately 0.05 (within reasonable range)
        # For small samples, p-value should be around 0.05-0.1
        assert 0.01 <= result["p_value"] <= 0.2, \
            f"Expected p_value between 0.01 and 0.2, got {result['p_value']}"
        
        # Check effect_size (Cohen's d) is approximately 1.5 (large effect)
        # For these values, Cohen's d should be around 1.5-2.0
        assert 1.0 <= result["effect_size"] <= 2.0, \
            f"Expected effect_size between 1.0 and 2.0, got {result['effect_size']}"

    def test_independent_t_test_identical_means(self):
        """Test with identical means - should have high p-value."""
        llm_data = [1, 2, 3, 4, 5]
        human_data = [1, 2, 3, 4, 5]
        
        result = statistical_tests.t_test(llm_data, human_data)
        
        assert result["p_value"] > 0.5, \
            f"Identical means should have high p-value, got {result['p_value']}"
        assert abs(result["t_statistic"]) < 0.01, \
            f"t-statistic should be near 0, got {result['t_statistic']}"

    def test_independent_t_test_effect_size_sign(self):
        """Test that effect size sign indicates direction of difference."""
        llm_data = [1, 2, 3]  # Lower values
        human_data = [4, 5, 6]  # Higher values
        
        result = statistical_tests.t_test(llm_data, human_data)
        
        # llm < human, so effect_size should be negative (llm - human)
        assert result["effect_size"] < 0, \
            f"Effect size should be negative when llm < human, got {result['effect_size']}"


class TestStatisticalUtilities:
    """Tests for statistical utility functions."""

    def test_cohen_d_calculation(self):
        """Test Cohen's d calculation with known values."""
        llm_data = [1, 2, 3, 4, 5]
        human_data = [6, 7, 8, 9, 10]
        
        result = statistical_tests.t_test(llm_data, human_data)
        
        # Manual calculation:
        # llm mean = 3, human mean = 8
        # llm std = sqrt(2) ≈ 1.414, human std = sqrt(2) ≈ 1.414
        # pooled std = sqrt((2 + 2) / 2) = sqrt(2) ≈ 1.414
        # Cohen's d = (3 - 8) / 1.414 ≈ -3.536
        
        expected_d = -3.536
        assert math.isclose(result["effect_size"], expected_d, abs_tol=0.1), \
            f"Expected Cohen's d ≈ {expected_d}, got {result['effect_size']}"

    def test_shapiro_wilk_normality_check(self):
        """Test Shapiro-Wilk normality test implementation."""
        # Normally distributed data
        normal_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        result = statistical_tests.shapiro_wilk_test(normal_data)
        
        assert "statistic" in result, "Result must contain statistic"
        assert "p_value" in result, "Result must contain p_value"
        assert 0 <= result["statistic"] <= 1, \
            f"Shapiro statistic should be between 0 and 1, got {result['statistic']}"
        assert 0 <= result["p_value"] <= 1, \
            f"Shapiro p-value should be between 0 and 1, got {result['p_value']}"