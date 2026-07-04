import pytest
import numpy as np
from code.src.audit.stat_verification import (
    two_proportion_z_test,
    welch_t_test,
    fisher_exact_test,
    verify_z_test_consistency,
    verify_welch_t_consistency,
    verify_fisher_consistency
)

class TestTwoProportionZTest:
    def test_basic_z_test(self):
        """Test basic z-test calculation with known values."""
        # Example: 50/1000 vs 75/1000
        z_stat, p_value = two_proportion_z_test(1000, 50, 1000, 75)
        
        assert 0 < z_stat < 10, "Z-statistic should be positive and reasonable"
        assert 0 < p_value < 1, "P-value should be between 0 and 1"
        assert p_value < 0.05, "Expected significant result for this example"

    def test_equal_proportions(self):
        """Test when proportions are equal, p-value should be 1.0."""
        z_stat, p_value = two_proportion_z_test(1000, 50, 1000, 50)
        
        assert abs(z_stat) < 1e-10, "Z-statistic should be ~0 for equal proportions"
        assert abs(p_value - 1.0) < 1e-6, "P-value should be 1.0 for equal proportions"

    def test_edge_case_zero_successes(self):
        """Test edge case with zero successes."""
        z_stat, p_value = two_proportion_z_test(1000, 0, 1000, 10)
        
        assert p_value < 1.0, "Should detect difference even with zero successes"

class TestWelchTTest:
    def test_basic_welch_test(self):
        """Test basic Welch t-test calculation."""
        # Example: mean1=100, mean2=110, std1=15, std2=18, n1=150, n2=150
        t_stat, p_value = welch_t_test(100, 110, 15, 18, 150, 150)
        
        assert 0 < abs(t_stat) < 10, "T-statistic should be reasonable"
        assert 0 < p_value < 1, "P-value should be between 0 and 1"

    def test_equal_means(self):
        """Test when means are equal, p-value should be 1.0."""
        t_stat, p_value = welch_t_test(100, 100, 15, 15, 100, 100)
        
        assert abs(t_stat) < 1e-10, "T-statistic should be ~0 for equal means"
        assert abs(p_value - 1.0) < 1e-6, "P-value should be 1.0 for equal means"

class TestFisherExactTest:
    def test_basic_fisher_test(self):
        """Test basic Fisher exact test calculation."""
        # 2x2 table: [[50, 950], [75, 925]]
        odds_ratio, p_value = fisher_exact_test(50, 950, 75, 925)
        
        assert odds_ratio > 0, "Odds ratio should be positive"
        assert 0 < p_value < 1, "P-value should be between 0 and 1"

    def test_perfect_separation(self):
        """Test edge case with perfect separation."""
        odds_ratio, p_value = fisher_exact_test(0, 100, 10, 90)
        
        assert p_value < 1.0, "Should detect difference in edge case"

class TestVerificationFunctions:
    def test_verify_z_test_consistency(self):
        """Test z-test verification function."""
        result = verify_z_test_consistency(1000, 50, 1000, 75, 0.032)
        
        assert "is_consistent" in result
        assert "calculated_p" in result
        assert "difference" in result
        assert result["test_type"] == "z-test"

    def test_verify_welch_t_consistency(self):
        """Test Welch t-test verification function."""
        result = verify_welch_t_consistency(100, 110, 15, 18, 150, 150, 0.025)
        
        assert "is_consistent" in result
        assert result["test_type"] == "welch-t"

    def test_verify_fisher_consistency(self):
        """Test Fisher exact test verification function."""
        result = verify_fisher_consistency(50, 950, 75, 925, 0.041)
        
        assert "is_consistent" in result
        assert result["test_type"] == "fisher"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
