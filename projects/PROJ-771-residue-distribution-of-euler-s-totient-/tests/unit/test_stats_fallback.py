import pytest
from code.stats import check_bin_counts_and_fallback, run_chi_squared_goodness_of_fit

def test_fallback_triggered_small_N():
    """Test that fallback triggers when expected bin count < 5."""
    # N=10, prime=3 -> expected = 3.33 < 5 -> should fallback
    observed = {0: 4, 1: 3, 2: 3}
    prime = 3
    needs_fallback, method = check_bin_counts_and_fallback(observed, prime)
    assert needs_fallback is True
    assert method == "monte_carlo"

def test_no_fallback_large_N():
    """Test that fallback does NOT trigger when expected bin count >= 5."""
    # N=100, prime=3 -> expected = 33.33 >= 5 -> no fallback
    observed = {0: 33, 1: 33, 2: 34}
    prime = 3
    needs_fallback, method = check_bin_counts_and_fallback(observed, prime)
    assert needs_fallback is False
    assert method == "exact"

def test_chi2_fallback_execution():
    """Test that run_chi_squared_goodness_of_fit actually runs the Monte Carlo fallback."""
    # Small N to trigger fallback
    observed = {0: 1, 1: 1, 2: 0} # N=2, prime=3 -> exp=0.66
    prime = 3
    
    result = run_chi_squared_goodness_of_fit(observed, prime)
    
    assert result.method == "monte_carlo"
    assert result.p_value is not None
    assert 0.0 <= result.p_value <= 1.0
    assert result.prime == prime
    assert result.N == 2

def test_chi2_exact_execution():
    """Test that run_chi_squared_goodness_of_fit runs exact test for large N."""
    # Large N to avoid fallback
    observed = {0: 34, 1: 33, 2: 33} # N=100, prime=3 -> exp=33.33
    prime = 3
    
    result = run_chi_squared_goodness_of_fit(observed, prime)
    
    assert result.method == "exact"
    assert result.p_value is not None
    assert 0.0 <= result.p_value <= 1.0

def test_bonferroni_correction():
    """Test that Bonferroni correction is calculated."""
    observed = {0: 33, 1: 33, 2: 34}
    prime = 3
    result = run_chi_squared_goodness_of_fit(observed, prime)
    
    assert result.bonferroni_passed is not None
    # Bonferroni alpha = 0.05/4 = 0.0125
    # If p_value > 0.0125, passed should be True
    # If p_value <= 0.0125, passed should be False
    expected_alpha = 0.05 / 4
    if result.p_value > expected_alpha:
        assert result.bonferroni_passed == True
    else:
        assert result.bonferroni_passed == False
