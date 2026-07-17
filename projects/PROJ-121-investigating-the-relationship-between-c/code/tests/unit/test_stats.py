import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from src.stats import (
    compute_lomb_scargle_periodogram,
    find_significant_peaks,
    compute_false_alarm_probability,
    compute_correlation_coefficient,
    compute_correlation_with_uncertainty,
    block_bootstrap_resample,
    monte_carlo_shuffle_test,
    bonferroni_corrected_pvalue,
    is_significant_after_bonferroni
)
from src.config import DEFAULT_BIN_SIZE_DAYS

@pytest.fixture
def sample_timeseries():
    """Generate sample time series for testing."""
    np.random.seed(42)
    n = 100
    time = np.arange(n) * 1.0  # Days
    # Create a signal with some noise
    signal = 0.5 * np.sin(2 * np.pi * time / 27.0) + np.random.normal(0, 0.1, n)
    return time, signal

def test_block_bootstrap_resample_adaptive_blocks():
    """
    Test block bootstrap with adaptive block length selection.
    Verifies FR-005: if n_blocks < 30, use 1x bin_size; else 2x bin_size.
    """
    np.random.seed(123)
    n = 50  # Small dataset to trigger adaptive behavior (< 30 blocks expected)
    time = np.arange(n) * 1.0
    anisotropy = np.random.normal(0, 1, n)
    solar_proxy = np.random.normal(0, 1, n)
    
    bin_size = DEFAULT_BIN_SIZE_DAYS  # 27 days
    
    result = block_bootstrap_resample(
        time, anisotropy, solar_proxy,
        bin_size_days=bin_size,
        n_bootstrap=10
    )
    
    # With n=50 and bin_size=27, estimated blocks ~ 50/(2*27/27) = 25 < 30
    # So block_length should be 1 * bin_size = 27
    expected_block_length = int(1.0 * bin_size)
    
    assert result['block_length'] == expected_block_length, \
        f"Expected block_length {expected_block_length}, got {result['block_length']}"
    assert result['n_blocks'] >= 1, "Should have at least 1 block"
    assert 'mean_corr' in result
    assert 'ci_lower' in result
    assert 'ci_upper' in result

def test_block_bootstrap_resample_long_series():
    """
    Test block bootstrap with long series (>= 30 blocks).
    Should use 2x bin_size.
    """
    np.random.seed(456)
    n = 500  # Large dataset to trigger standard behavior
    time = np.arange(n) * 1.0
    anisotropy = np.random.normal(0, 1, n)
    solar_proxy = np.random.normal(0, 1, n)
    
    bin_size = DEFAULT_BIN_SIZE_DAYS
    
    result = block_bootstrap_resample(
        time, anisotropy, solar_proxy,
        bin_size_days=bin_size,
        n_bootstrap=10
    )
    
    # With n=500, estimated blocks ~ 500/(2*27/27) = 250 >= 30
    # So block_length should be 2 * bin_size = 54
    expected_block_length = int(2.0 * bin_size)
    
    assert result['block_length'] == expected_block_length, \
        f"Expected block_length {expected_block_length}, got {result['block_length']}"
    assert result['n_blocks'] >= 30, "Should have >= 30 blocks for standard logic"

def test_block_bootstrap_with_small_blocks():
    """Test block bootstrap with very small dataset."""
    np.random.seed(789)
    n = 10
    time = np.arange(n) * 1.0
    anisotropy = np.random.normal(0, 1, n)
    solar_proxy = np.random.normal(0, 1, n)
    
    result = block_bootstrap_resample(
        time, anisotropy, solar_proxy,
        bin_size_days=27,
        n_bootstrap=5
    )
    
    # Should handle small datasets gracefully
    assert 'mean_corr' in result
    assert 'n_blocks' in result
    assert result['block_length'] >= 1

def test_monte_carlo_shuffle_test_basic():
    """Test basic Monte-Carlo shuffle test functionality."""
    np.random.seed(999)
    n = 50
    time = np.arange(n) * 1.0
    anisotropy = np.random.normal(0, 1, n)
    solar_proxy = np.random.normal(0, 1, n)
    
    result = monte_carlo_shuffle_test(
        time, anisotropy, solar_proxy,
        n_permutations=20  # Small for testing
    )
    
    assert 'observed_correlation' in result
    assert 'mc_p_value' in result
    assert 'null_mean' in result
    assert 'n_permutations' in result
    assert result['n_permutations'] <= 20  # May be less if some failed

def test_monte_carlo_significance_detection():
    """Test MC test with known correlation."""
    np.random.seed(555)
    n = 100
    time = np.arange(n) * 1.0
    # Create correlated data
    anisotropy = np.random.normal(0, 1, n)
    solar_proxy = 0.8 * anisotropy + np.random.normal(0, 0.2, n)
    
    result = monte_carlo_shuffle_test(
        time, anisotropy, solar_proxy,
        n_permutations=50
    )
    
    # With strong correlation, p-value should be low
    assert result['mc_p_value'] < 0.5, "Should detect significant correlation"
    assert abs(result['observed_correlation']) > 0.5

def test_monte_carlo_no_correlation():
    """Test MC test with uncorrelated data."""
    np.random.seed(111)
    n = 100
    time = np.arange(n) * 1.0
    anisotropy = np.random.normal(0, 1, n)
    solar_proxy = np.random.normal(0, 1, n)
    
    result = monte_carlo_shuffle_test(
        time, anisotropy, solar_proxy,
        n_permutations=50
    )
    
    # With no correlation, p-value should be high (not significant)
    assert result['mc_p_value'] > 0.1, "Should not detect spurious correlation"

def test_compute_correlation_with_uncertainty():
    """Test correlation with bootstrap uncertainty."""
    np.random.seed(333)
    n = 50
    x = np.random.normal(0, 1, n)
    y = 0.5 * x + np.random.normal(0, 0.5, n)
    
    result = compute_correlation_with_uncertainty(x, y, n_bootstrap=100)
    
    assert 'correlation' in result
    assert 'ci_lower' in result
    assert 'ci_upper' in result
    assert result['ci_lower'] <= result['correlation'] <= result['ci_upper']

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.05, 0.1, 0.5]
    result = bonferroni_corrected_pvalue(p_values, alpha=0.05)
    
    assert len(result['corrected_pvalues']) == 4
    assert result['corrected_alpha'] == 0.05 / 4
    assert result['n_tests'] == 4

def test_is_significant_after_bonferroni():
    """Test individual significance check."""
    assert is_significant_after_bonferroni(0.01, 4, 0.05)
    assert not is_significant_after_bonferroni(0.02, 4, 0.05)  # 0.02 > 0.0125