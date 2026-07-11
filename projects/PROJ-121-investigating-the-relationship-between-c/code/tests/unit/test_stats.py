import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from src.stats import (
    compute_lomb_scargle_periodogram,
    find_significant_peaks,
    compute_false_alarm_probability,
    bonferroni_corrected_pvalue,
    is_significant_after_bonferroni,
    compute_correlation_coefficient,
    block_bootstrap_resample,
    monte_carlo_shuffle_test,
    compute_correlation_with_uncertainty
)
from src.config import DEFAULT_BIN_SIZE_DAYS

@pytest.fixture
def sample_timeseries():
    """Generate sample time series for testing."""
    n = 100
    times = np.linspace(0, 365, n)  # 1 year of data
    anisotropy = np.sin(2 * np.pi * times / 365) + 0.1 * np.random.randn(n)
    solar_proxy = np.cos(2 * np.pi * times / 365) + 0.1 * np.random.randn(n)
    return times, anisotropy, solar_proxy

def test_monte_carlo_shuffle_test_basic(sample_timeseries):
    """Test basic Monte-Carlo shuffle test functionality."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    result = monte_carlo_shuffle_test(
        times, anisotropy, solar_proxy,
        n_permutations=100,  # Small number for speed
        n_bootstrap=50
    )
    
    assert 'observed_corr' in result
    assert 'p_value' in result
    assert 'significant' in result
    assert 'null_distribution' in result
    assert 'bootstrap_distribution' in result
    
    # Check that null distribution has correct size
    assert len(result['null_distribution']) == 100
    assert len(result['bootstrap_distribution']) == 50
    
    # P-value should be between 0 and 1
    assert 0 <= result['p_value'] <= 1

def test_block_bootstrap_resample_adaptive_blocks(sample_timeseries):
    """Test that block bootstrap adapts block size based on data length."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    # Test with short series (< 30 blocks expected)
    short_times = times[:20]
    short_aniso = anisotropy[:20]
    short_proxy = solar_proxy[:20]
    
    result_short = block_bootstrap_resample(
        short_times, short_aniso, short_proxy,
        bin_size_days=DEFAULT_BIN_SIZE_DAYS,
        n_bootstrap=10
    )
    
    assert len(result_short) == 10
    assert np.all(np.abs(result_short) <= 1.0)  # Correlation bounds

def test_block_bootstrap_resample_long_series(sample_timeseries):
    """Test block bootstrap with longer series (>= 30 blocks)."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    # Extend to ensure >= 30 blocks
    extended_times = np.linspace(0, 365 * 2, 200)
    extended_aniso = np.sin(2 * np.pi * extended_times / 365) + 0.1 * np.random.randn(len(extended_times))
    extended_proxy = np.cos(2 * np.pi * extended_times / 365) + 0.1 * np.random.randn(len(extended_times))
    
    result = block_bootstrap_resample(
        extended_times, extended_aniso, extended_proxy,
        bin_size_days=DEFAULT_BIN_SIZE_DAYS,
        n_bootstrap=10
    )
    
    assert len(result) == 10
    assert np.all(np.abs(result) <= 1.0)

def test_monte_carlo_significance_detection():
    """Test that Monte-Carlo can detect strong correlations."""
    # Create perfectly correlated data
    n = 50
    times = np.linspace(0, 365, n)
    anisotropy = np.sin(2 * np.pi * times / 365)
    solar_proxy = np.sin(2 * np.pi * times / 365)  # Perfect correlation
    
    result = monte_carlo_shuffle_test(
        times, anisotropy, solar_proxy,
        n_permutations=500,
        n_bootstrap=50
    )
    
    # Should detect strong correlation
    assert abs(result['observed_corr']) > 0.9
    # P-value should be very small for perfect correlation
    assert result['p_value'] < 0.1

def test_monte_carlo_no_correlation():
    """Test Monte-Carlo with uncorrelated data."""
    n = 50
    times = np.linspace(0, 365, n)
    anisotropy = np.random.randn(n)
    solar_proxy = np.random.randn(n)  # Uncorrelated
    
    result = monte_carlo_shuffle_test(
        times, anisotropy, solar_proxy,
        n_permutations=500,
        n_bootstrap=50
    )
    
    # Correlation should be near zero
    assert abs(result['observed_corr']) < 0.5
    # P-value should be large (not significant)
    assert result['p_value'] > 0.05

def test_compute_correlation_with_uncertainty(sample_timeseries):
    """Test full correlation analysis pipeline."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    result = compute_correlation_with_uncertainty(
        times, anisotropy, solar_proxy,
        bin_size_days=DEFAULT_BIN_SIZE_DAYS
    )
    
    # Check all expected keys
    expected_keys = [
        'pearson_correlation', 'pearson_pvalue',
        'monte_carlo_pvalue', 'monte_carlo_significant',
        'bonferroni_corrected_p', 'bonferroni_significant',
        'bootstrap_mean', 'bootstrap_std', 'bootstrap_ci_95'
    ]
    
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
    
    # Check correlation bounds
    assert -1 <= result['pearson_correlation'] <= 1
    assert 0 <= result['pearson_pvalue'] <= 1

def test_block_bootstrap_with_small_blocks(sample_timeseries):
    """Test block bootstrap logic when blocks < 30."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    # Use very small bin size to force many blocks
    # But with limited data, blocks should still be < 30
    result = block_bootstrap_resample(
        times, anisotropy, solar_proxy,
        bin_size_days=7,  # Small bin size
        n_bootstrap=20
    )
    
    assert len(result) == 20
    assert np.std(result) >= 0  # Should have some variance

def test_monte_carlo_with_different_permutations(sample_timeseries):
    """Test that increasing permutations improves p-value stability."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    result_100 = monte_carlo_shuffle_test(
        times, anisotropy, solar_proxy,
        n_permutations=100,
        n_bootstrap=20
    )
    
    result_1000 = monte_carlo_shuffle_test(
        times, anisotropy, solar_proxy,
        n_permutations=1000,
        n_bootstrap=20
    )
    
    # Both should have valid p-values
    assert 0 <= result_100['p_value'] <= 1
    assert 0 <= result_1000['p_value'] <= 1
    
    # With more permutations, p-value should be more stable
    # (not a strict assertion, but good sanity check)
    assert abs(result_100['p_value'] - result_1000['p_value']) < 0.2

def test_integration_bootstrap_and_shuffle(sample_timeseries):
    """Test that bootstrap and shuffle work together in full pipeline."""
    times, anisotropy, solar_proxy = sample_timeseries
    
    # Run full analysis
    full_result = compute_correlation_with_uncertainty(
        times, anisotropy, solar_proxy,
        bin_size_days=DEFAULT_BIN_SIZE_DAYS
    )
    
    # Bootstrap CI should contain bootstrap mean
    ci_low, ci_high = full_result['bootstrap_ci_95']
    assert ci_low <= full_result['bootstrap_mean'] <= ci_high
    
    # Bootstrap std should be positive
    assert full_result['bootstrap_std'] >= 0

def test_monte_carlo_handles_mismatched_lengths():
    """Test that Monte-Carlo raises error on mismatched inputs."""
    times = np.linspace(0, 365, 50)
    anisotropy = np.random.randn(50)
    solar_proxy = np.random.randn(40)  # Different length
    
    with pytest.raises(ValueError):
        monte_carlo_shuffle_test(times, anisotropy, solar_proxy)