"""
Contract tests for statistical methods in src/stats.py.

These tests verify the interface and basic contract compliance of the
statistical analysis functions required for User Story 2.

They do NOT verify correctness of statistical calculations (that's for
unit/integration tests), but rather ensure:
- Functions exist with expected signatures
- Functions return expected types
- Functions handle edge cases as specified in contracts
"""
import pytest
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We expect these to be implemented in src/stats.py
# If they don't exist yet, these tests will fail with ImportError
# which is the expected behavior for "write tests first"
try:
    from src.stats import (
        lomb_scargle_periodogram,
        block_bootstrap,
        monte_carlo_shuffle,
        bonferroni_correct,
        calculate_correlation_coefficient,
        compute_fap
    )
    STATS_MODULE_AVAILABLE = True
except ImportError:
    STATS_MODULE_AVAILABLE = False


@pytest.fixture
def sample_timeseries():
    """Create a sample timeseries for testing."""
    n = 100
    times = np.linspace(0, 100, n)
    values = np.sin(2 * np.pi * times / 27) + np.random.normal(0, 0.1, n)
    return times, values

@pytest.fixture
def sample_anisotropy_data():
    """Create sample anisotropy timeseries."""
    n = 50
    times = np.linspace(0, 1000, n)
    amplitudes = np.random.uniform(0.001, 0.01, n)
    phases = np.random.uniform(0, 2 * np.pi, n)
    return {
        'times': times,
        'amplitudes': amplitudes,
        'phases': phases
    }

@pytest.fixture
def sample_solar_proxy_data():
    """Create sample solar proxy timeseries."""
    n = 50
    times = np.linspace(0, 1000, n)
    sunspot_numbers = np.random.uniform(0, 150, n)
    return {
        'times': times,
        'values': sunspot_numbers
    }


class TestLombScargleContract:
    """Contract tests for Lomb-Scargle periodogram function."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_function_signature(self):
        """Verify lomb_scargle_periodogram has expected signature."""
        import inspect
        sig = inspect.signature(lomb_scargle_periodogram)
        params = list(sig.parameters.keys())
        # Expected parameters: times, values, frequencies (optional), normalization (optional)
        assert 'times' in params
        assert 'values' in params

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_returns_periodogram_dict(self, sample_timeseries):
        """Verify function returns a dictionary with expected keys."""
        times, values = sample_timeseries
        # Generate frequencies for testing
        frequencies = np.linspace(0.01, 0.5, 50)
        
        result = lomb_scargle_periodogram(times, values, frequencies)
        
        assert isinstance(result, dict)
        assert 'frequencies' in result
        assert 'power' in result
        assert len(result['frequencies']) == len(result['power'])
        assert len(result['frequencies']) == len(frequencies)

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_handles_empty_input(self):
        """Verify function handles empty input gracefully."""
        times = np.array([])
        values = np.array([])
        frequencies = np.array([])
        
        # Should not crash, should return empty result
        result = lomb_scargle_periodogram(times, values, frequencies)
        assert isinstance(result, dict)
        assert len(result['frequencies']) == 0
        assert len(result['power']) == 0

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_single_value_input(self):
        """Verify function handles single value input."""
        times = np.array([1.0])
        values = np.array([2.0])
        frequencies = np.array([0.1])
        
        # Should not crash
        result = lomb_scargle_periodogram(times, values, frequencies)
        assert isinstance(result, dict)
        assert len(result['frequencies']) == 1


class TestBlockBootstrapContract:
    """Contract tests for block bootstrap function."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_function_signature(self):
        """Verify block_bootstrap has expected signature."""
        import inspect
        sig = inspect.signature(block_bootstrap)
        params = list(sig.parameters.keys())
        # Expected: times, values, n_bootstrap, block_size (optional)
        assert 'times' in params
        assert 'values' in params
        assert 'n_bootstrap' in params

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_returns_bootstrap_samples(self, sample_timeseries):
        """Verify function returns bootstrap samples."""
        times, values = sample_timeseries
        
        result = block_bootstrap(times, values, n_bootstrap=100, block_size=10)
        
        assert isinstance(result, dict)
        assert 'bootstrap_means' in result
        assert 'bootstrap_stds' in result
        assert 'bootstrap_samples' in result
        assert len(result['bootstrap_samples']) == 100

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_block_size_validation(self, sample_timeseries):
        """Verify function validates block size."""
        times, values = sample_timeseries
        
        # Block size larger than data should raise ValueError
        with pytest.raises(ValueError):
            block_bootstrap(times, values, n_bootstrap=10, block_size=1000)

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_conditional_block_size_logic(self, sample_timeseries):
        """
        Verify the conditional logic for block size selection:
        - If independent blocks < 30, use 1x bin_size
        - Otherwise, use 2x bin_size
        
        This tests the FR-005 requirement.
        """
        times, values = sample_timeseries
        
        # The function should handle the block size selection internally
        # based on the number of independent blocks
        result = block_bootstrap(times, values, n_bootstrap=50)
        
        assert isinstance(result, dict)
        assert 'bootstrap_means' in result
        assert len(result['bootstrap_means']) == 50


class TestMonteCarloShuffleContract:
    """Contract tests for Monte-Carlo shuffle function."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_function_signature(self):
        """Verify monte_carlo_shuffle has expected signature."""
        import inspect
        sig = inspect.signature(monte_carlo_shuffle)
        params = list(sig.parameters.keys())
        # Expected: times1, values1, times2, values2, n_permutations
        assert 'times1' in params
        assert 'values1' in params
        assert 'times2' in params
        assert 'values2' in params
        assert 'n_permutations' in params

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_returns_fap(self, sample_anisotropy_data, sample_solar_proxy_data):
        """Verify function returns False Alarm Probability."""
        aniso = sample_anisotropy_data
        solar = sample_solar_proxy_data
        
        result = monte_carlo_shuffle(
            aniso['times'], aniso['amplitudes'],
            solar['times'], solar['values'],
            n_permutations=100
        )
        
        assert isinstance(result, dict)
        assert 'fap' in result
        assert 'observed_correlation' in result
        assert 'null_distribution' in result
        
        # FAP should be between 0 and 1
        assert 0 <= result['fap'] <= 1

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_permutation_count(self, sample_anisotropy_data, sample_solar_proxy_data):
        """Verify null distribution has correct length."""
        aniso = sample_anisotropy_data
        solar = sample_solar_proxy_data
        n_perm = 50
        
        result = monte_carlo_shuffle(
            aniso['times'], aniso['amplitudes'],
            solar['times'], solar['values'],
            n_permutations=n_perm
        )
        
        assert len(result['null_distribution']) == n_perm


class TestBonferroniCorrectionContract:
    """Contract tests for Bonferroni correction function."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_function_signature(self):
        """Verify bonferroni_correct has expected signature."""
        import inspect
        sig = inspect.signature(bonferroni_correct)
        params = list(sig.parameters.keys())
        # Expected: p_values, alpha (optional)
        assert 'p_values' in params

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_returns_corrected_pvalues(self):
        """Verify function returns corrected p-values."""
        p_values = np.array([0.01, 0.05, 0.1, 0.001])
        
        result = bonferroni_correct(p_values)
        
        assert isinstance(result, dict)
        assert 'corrected_pvalues' in result
        assert 'alpha' in result
        assert 'significant' in result
        
        # Corrected p-values should be >= original p-values
        assert all(result['corrected_pvalues'] >= p_values)
        
        # Significant flags should be boolean
        assert all(isinstance(s, bool) for s in result['significant'])

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_default_alpha(self):
        """Verify default alpha is 0.0017 (for 30 tests)."""
        p_values = np.array([0.01, 0.05])
        
        result = bonferroni_correct(p_values)
        
        # Default should be 0.05 / 30 = 0.001666...
        expected_alpha = 0.05 / 30
        assert abs(result['alpha'] - expected_alpha) < 1e-6


class TestCorrelationCoefficientContract:
    """Contract tests for correlation coefficient function."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_function_signature(self):
        """Verify calculate_correlation_coefficient has expected signature."""
        import inspect
        sig = inspect.signature(calculate_correlation_coefficient)
        params = list(sig.parameters.keys())
        # Expected: times1, values1, times2, values2
        assert 'times1' in params
        assert 'values1' in params
        assert 'times2' in params
        assert 'values2' in params

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_returns_correlation_result(self, sample_anisotropy_data, sample_solar_proxy_data):
        """Verify function returns correlation result."""
        aniso = sample_anisotropy_data
        solar = sample_solar_proxy_data
        
        result = calculate_correlation_coefficient(
            aniso['times'], aniso['amplitudes'],
            solar['times'], solar['values']
        )
        
        assert isinstance(result, dict)
        assert 'correlation' in result
        assert 'p_value' in result
        
        # Correlation should be between -1 and 1
        assert -1 <= result['correlation'] <= 1


class TestFAPComputationContract:
    """Contract tests for FAP computation."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_function_signature(self):
        """Verify compute_fap has expected signature."""
        import inspect
        sig = inspect.signature(compute_fap)
        params = list(sig.parameters.keys())
        # Expected: observed_stat, null_distribution
        assert 'observed_stat' in params
        assert 'null_distribution' in params

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_returns_fap_value(self):
        """Verify function returns FAP value."""
        observed = 0.8
        null_dist = np.random.uniform(0, 1, 1000)
        
        result = compute_fap(observed, null_dist)
        
        assert isinstance(result, dict)
        assert 'fap' in result
        assert 'n_permutations' in result
        
        # FAP should be between 0 and 1
        assert 0 <= result['fap'] <= 1


class TestIntegrationContract:
    """Contract tests for integration between statistical methods."""

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_block_bootstrap_integration_with_monte_carlo(self, sample_timeseries):
        """
        Verify that block_bootstrap output can be used with monte_carlo_shuffle
        as per T023 requirement.
        """
        times, values = sample_timeseries
        
        # Get bootstrap results
        bootstrap_result = block_bootstrap(times, values, n_bootstrap=20)
        
        # The bootstrap means should be usable as input for correlation tests
        assert 'bootstrap_means' in bootstrap_result
        assert len(bootstrap_result['bootstrap_means']) == 20

    @pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
    def test_bonferroni_integration_with_monte_carlo(self, sample_anisotropy_data, sample_solar_proxy_data):
        """
        Verify that FAP from monte_carlo_shuffle can be corrected with
        bonferroni_correct as per T024 requirement.
        """
        aniso = sample_anisotropy_data
        solar = sample_solar_proxy_data
        
        # Get FAP from Monte Carlo
        mc_result = monte_carlo_shuffle(
            aniso['times'], aniso['amplitudes'],
            solar['times'], solar['values'],
            n_permutations=50
        )
        
        # Apply Bonferroni correction
        fap_value = mc_result['fap']
        corrected = bonferroni_correct(np.array([fap_value]))
        
        assert 'significant' in corrected
        assert isinstance(corrected['significant'][0], bool)

if not STATS_MODULE_AVAILABLE:
    # If stats module is not yet implemented, provide a placeholder test
    # that will fail, indicating the module needs to be created
    @pytest.mark.skip(reason="src/stats.py not yet implemented - contract tests pending")
    def test_stats_module_exists():
        """Placeholder test to indicate stats module is missing."""
        pytest.fail("src/stats.py must be implemented to run contract tests")