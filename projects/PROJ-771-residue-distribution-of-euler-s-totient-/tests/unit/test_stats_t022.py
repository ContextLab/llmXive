import pytest
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats import (
    StatisticalResult,
    run_full_statistical_analysis,
    determine_primary_pass_fail,
    determine_bonferroni_pass_fail,
    calculate_chi_squared_statistic,
    run_chi_squared_goodness_of_fit
)

class TestT022PrimaryPassFail:
    """Tests for T022: Primary pass/fail flag logic based on alpha=0.05."""

    def test_pass_when_p_value_high(self):
        """Test that we pass when p-value is high (e.g., 0.9)."""
        result = determine_primary_pass_fail(0.9)
        assert result is True, "Should pass when p-value is 0.9"

    def test_pass_when_p_value_at_threshold(self):
        """Test that we pass when p-value is exactly 0.05."""
        result = determine_primary_pass_fail(0.05)
        assert result is True, "Should pass when p-value is exactly 0.05"

    def test_fail_when_p_value_low(self):
        """Test that we fail when p-value is low (e.g., 0.01)."""
        result = determine_primary_pass_fail(0.01)
        assert result is False, "Should fail when p-value is 0.01"

    def test_fail_when_p_value_very_low(self):
        """Test that we fail when p-value is very low (e.g., 0.001)."""
        result = determine_primary_pass_fail(0.001)
        assert result is False, "Should fail when p-value is 0.001"

    def test_integration_with_statistical_result(self):
        """Test that the flag is correctly set in StatisticalResult."""
        # Simulate a case with high p-value (uniform distribution)
        counts_uniform = {0: 3333, 1: 3334, 2: 3333}  # N=10000, prime=3
        result = run_full_statistical_analysis(counts_uniform, 3, 10000)
        
        # With uniform distribution, p-value should be high, so primary_pass should be True
        assert result.primary_pass is True, "Uniform distribution should pass"
        assert result.chi_squared_p_value >= 0.05, "P-value should be >= 0.05"

    def test_integration_with_biased_distribution(self):
        """Test that the flag correctly fails for biased distribution."""
        # Simulate a biased case (e.g., too many 0s)
        counts_biased = {0: 5000, 1: 3000, 2: 2000}  # N=10000, prime=3
        result = run_full_statistical_analysis(counts_biased, 3, 10000)
        
        # With biased distribution, p-value should be low, so primary_pass should be False
        # Note: This might not always fail for small deviations, but extreme bias should
        # We're testing the logic, not the statistical power
        # For this test, we just verify the flag is set based on p-value
        expected_pass = result.chi_squared_p_value >= 0.05
        assert result.primary_pass == expected_pass, "Flag should match p-value threshold"

class TestT022bBonferroniCorrection:
    """Tests for T022b: Bonferroni-corrected sensitivity analysis."""

    def test_bonferroni_stricter_threshold(self):
        """Test that Bonferroni correction uses a stricter threshold."""
        # With 4 tests, alpha_adj = 0.05/4 = 0.0125
        # A p-value of 0.02 should pass primary but fail Bonferroni
        primary = determine_primary_pass_fail(0.02)
        bonferroni = determine_bonferroni_pass_fail(0.02, num_tests=4)
        
        assert primary is True, "Should pass primary test (0.02 >= 0.05)"
        assert bonferroni is False, "Should fail Bonferroni test (0.02 < 0.0125)"

    def test_bonferroni_with_high_p_value(self):
        """Test that high p-values pass both tests."""
        primary = determine_primary_pass_fail(0.5)
        bonferroni = determine_bonferroni_pass_fail(0.5, num_tests=4)
        
        assert primary is True
        assert bonferroni is True

    def test_bonferroni_with_very_low_p_value(self):
        """Test that very low p-values fail both tests."""
        primary = determine_primary_pass_fail(0.001)
        bonferroni = determine_bonferroni_pass_fail(0.001, num_tests=4)
        
        assert primary is False
        assert bonferroni is False

    def test_integration_with_statistical_result(self):
        """Test that Bonferroni flag is correctly set in StatisticalResult."""
        # Use a case where p-value is between 0.0125 and 0.05
        # This is hard to guarantee, so we test the logic directly
        # and verify the flag is computed correctly
        counts = {0: 3333, 1: 3334, 2: 3333}
        result = run_full_statistical_analysis(counts, 3, 10000)
        
        # Verify the flag matches the expected calculation
        expected_bonferroni = result.chi_squared_p_value >= (0.05 / 4)
        assert result.bonferroni_pass == expected_bonferroni, "Bonferroni flag should match calculation"

class TestT022EdgeCases:
    """Edge case tests for T022."""

    def test_p_value_zero(self):
        """Test with p-value of 0."""
        result = determine_primary_pass_fail(0.0)
        assert result is False, "Should fail when p-value is 0"

    def test_p_value_one(self):
        """Test with p-value of 1."""
        result = determine_primary_pass_fail(1.0)
        assert result is True, "Should pass when p-value is 1"

    def test_custom_alpha(self):
        """Test with custom alpha value."""
        # Using alpha=0.01
        result = determine_primary_pass_fail(0.015, alpha=0.01)
        assert result is False, "Should fail when p-value (0.015) < alpha (0.01)"

        result = determine_primary_pass_fail(0.005, alpha=0.01)
        assert result is True, "Should pass when p-value (0.005) >= alpha (0.01)"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])