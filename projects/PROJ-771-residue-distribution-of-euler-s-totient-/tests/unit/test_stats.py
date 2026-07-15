import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from stats import (
    check_bin_counts_and_fallback,
    run_chi_squared_goodness_of_fit,
    calculate_deviation_D,
    StatisticalResult
)

class TestCheckBinCountsAndFallback:
    """
    Unit tests for check_bin_counts_and_fallback function.
    Tests the FR-003 fallback logic for small bin counts.
    """
    
    def test_fallback_triggered_small_n(self):
        """Test that fallback is triggered when expected count < 5"""
        # N = 12, prime = 3 => expected = 4.0 < 5
        residue_counts = [4, 4, 4]
        prime = 3
        
        needs_fallback, reason = check_bin_counts_and_fallback(residue_counts, prime)
        
        assert needs_fallback is True
        assert "fallback" in reason.lower() or "expected count" in reason.lower()
    
    def test_fallback_triggered_very_small_n(self):
        """Test fallback with very small N"""
        # N = 6, prime = 3 => expected = 2.0 < 5
        residue_counts = [2, 2, 2]
        prime = 3
        
        needs_fallback, reason = check_bin_counts_and_fallback(residue_counts, prime)
        
        assert needs_fallback is True
    
    def test_no_fallback_large_n(self):
        """Test that no fallback is triggered when expected count >= 5"""
        # N = 15, prime = 3 => expected = 5.0 >= 5
        residue_counts = [5, 5, 5]
        prime = 3
        
        needs_fallback, reason = check_bin_counts_and_fallback(residue_counts, prime)
        
        assert needs_fallback is False
        assert reason is None
    
    def test_fallback_triggered_edge_case(self):
        """Test fallback at boundary (expected = 4.9)"""
        # N = 14.7 (not possible with integers, but test with 14)
        # N = 14, prime = 3 => expected = 4.67 < 5
        residue_counts = [5, 5, 4]
        prime = 3
        
        needs_fallback, reason = check_bin_counts_and_fallback(residue_counts, prime)
        
        assert needs_fallback is True
    
    def test_different_prime(self):
        """Test with prime = 5"""
        # N = 20, prime = 5 => expected = 4.0 < 5
        residue_counts = [4, 4, 4, 4, 4]
        prime = 5
        
        needs_fallback, reason = check_bin_counts_and_fallback(residue_counts, prime)
        
        assert needs_fallback is True
    
    def test_different_prime_no_fallback(self):
        """Test with prime = 5, large N"""
        # N = 50, prime = 5 => expected = 10.0 >= 5
        residue_counts = [10, 10, 10, 10, 10]
        prime = 5
        
        needs_fallback, reason = check_bin_counts_and_fallback(residue_counts, prime)
        
        assert needs_fallback is False

class TestRunChiSquaredGoodnessOfFit:
    """
    Unit tests for run_chi_squared_goodness_of_fit function.
    """
    
    def test_uniform_distribution_pass(self):
        """Test that uniform distribution yields high p-value"""
        # Perfectly uniform distribution
        residue_counts = [100, 100, 100]
        prime = 3
        
        result = run_chi_squared_goodness_of_fit(residue_counts, prime)
        
        assert result.prime == prime
        assert result.N == 300
        assert len(result.observed_counts) == 3
        assert result.passed is True  # p-value should be high
        assert result.method in ["standard", "monte_carlo"]
    
    def test_biased_distribution_fail(self):
        """Test that biased distribution yields low p-value"""
        # Heavily biased distribution
        residue_counts = [200, 50, 50]
        prime = 3
        
        result = run_chi_squared_goodness_of_fit(residue_counts, prime)
        
        assert result.prime == prime
        assert result.passed is False  # p-value should be low
    
    def test_small_n_fallback(self):
        """Test that small N triggers Monte Carlo method"""
        # Small N that triggers fallback
        residue_counts = [4, 4, 4]
        prime = 3
        
        result = run_chi_squared_goodness_of_fit(residue_counts, prime)
        
        assert result.method == "monte_carlo"
        assert result.prime == prime
    
    def test_deviation_D_calculation(self):
        """Test that deviation D is calculated correctly"""
        # O = [10, 20, 30], E = [20, 20, 20]
        # D = max(|10-20|, |20-20|, |30-20|) = max(10, 0, 10) = 10
        residue_counts = [10, 20, 30]
        prime = 3
        
        result = run_chi_squared_goodness_of_fit(residue_counts, prime)
        
        assert result.deviation_D == 10.0

class TestCalculateDeviationD:
    """
    Unit tests for calculate_deviation_D function.
    """
    
    def test_perfect_uniform(self):
        """Test D = 0 for perfect uniform"""
        observed = [10, 10, 10]
        expected = [10.0, 10.0, 10.0]
        
        D = calculate_deviation_D(observed, expected)
        assert D == 0.0
    
    def test_simple_deviation(self):
        """Test D calculation with simple deviation"""
        observed = [5, 15]
        expected = [10.0, 10.0]
        
        D = calculate_deviation_D(observed, expected)
        assert D == 5.0
    
    def test_multiple_deviations(self):
        """Test D with multiple deviations, max should be returned"""
        observed = [2, 8, 15]
        expected = [8.33, 8.33, 8.33]  # Approximate
        
        # Expected is calculated as total/3 = 25/3 = 8.33
        # D = max(|2-8.33|, |8-8.33|, |15-8.33|) = max(6.33, 0.33, 6.67) = 6.67
        D = calculate_deviation_D(observed, expected)
        assert abs(D - 6.67) < 0.1  # Allow small floating point error
    
    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise error"""
        with pytest.raises(ValueError):
            calculate_deviation_D([1, 2], [1.0, 2.0, 3.0])