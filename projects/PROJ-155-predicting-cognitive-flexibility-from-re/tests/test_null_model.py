"""
Unit tests for null-model validation (phase-shuffled surrogates).

This module verifies the correctness of the phase-shuffling implementation
used to generate surrogate null models for validating dynamic connectivity metrics.
"""

import pytest
import numpy as np
from scipy.fft import fft, ifft
from code.features.null_model import (
    phase_shuffle,
    generate_phase_shuffled_surrogates,
    compute_surrogate_variability,
    validate_metric_significance
)
from code.config import set_seed


class TestPhaseShuffle:
    """Tests for the phase_shuffle function."""

    def test_preserves_amplitude_spectrum(self):
        """Verify that phase shuffling preserves the amplitude spectrum."""
        set_seed(42)
        # Create a deterministic signal
        t = np.linspace(0, 10, 1000)
        signal = np.sin(2 * np.pi * 1 * t) + 0.5 * np.sin(2 * np.pi * 3 * t)
        
        # Get original amplitude spectrum
        original_fft = np.abs(fft(signal))
        
        # Phase shuffle
        shuffled = phase_shuffle(signal)
        shuffled_fft = np.abs(fft(shuffled))
        
        # Amplitudes should be identical (within floating point precision)
        np.testing.assert_array_almost_equal(original_fft, shuffled_fft, decimal=10)

    def test_changes_phase_spectrum(self):
        """Verify that phase shuffling actually changes the phase."""
        set_seed(42)
        signal = np.random.randn(500)
        
        original_phase = np.angle(fft(signal))
        shuffled = phase_shuffle(signal)
        shuffled_phase = np.angle(fft(shuffled))
        
        # Phase should be different (unless by extreme chance)
        # We check that the difference is not all zeros
        phase_diff = np.abs(original_phase - shuffled_phase)
        assert not np.allclose(phase_diff, 0), "Phase shuffling did not change the phase"

    def test_preserves_mean_and_variance(self):
        """Verify that phase shuffling preserves mean and variance."""
        set_seed(42)
        signal = np.random.randn(1000)
        
        shuffled = phase_shuffle(signal)
        
        np.testing.assert_almost_equal(np.mean(signal), np.mean(shuffled), decimal=10)
        np.testing.assert_almost_equal(np.var(signal), np.var(shuffled), decimal=10)

    def test_output_shape_matches_input(self):
        """Verify output shape matches input shape."""
        set_seed(42)
        signal = np.random.randn(500)
        
        shuffled = phase_shuffle(signal)
        
        assert shuffled.shape == signal.shape

    def test_deterministic_with_seed(self):
        """Verify deterministic output when seed is set."""
        set_seed(42)
        signal = np.random.randn(500)
        
        shuffled1 = phase_shuffle(signal)
        
        set_seed(42)
        shuffled2 = phase_shuffle(signal)
        
        np.testing.assert_array_equal(shuffled1, shuffled2)

    def test_2d_array_handling(self):
        """Test phase shuffling on 2D arrays (time x features)."""
        set_seed(42)
        # 2D array: 500 timepoints x 200 features
        signal_2d = np.random.randn(500, 200)
        
        shuffled_2d = phase_shuffle(signal_2d)
        
        assert shuffled_2d.shape == signal_2d.shape
        # Check that each feature column was shuffled independently
        for i in range(signal_2d.shape[1]):
            original_fft = np.abs(fft(signal_2d[:, i]))
            shuffled_fft = np.abs(fft(shuffled_2d[:, i]))
            np.testing.assert_array_almost_equal(original_fft, shuffled_fft, decimal=10)

class TestGeneratePhaseShuffledSurrogates:
    """Tests for generating multiple phase-shuffled surrogates."""

    def test_generates_correct_number(self):
        """Verify correct number of surrogates generated."""
        set_seed(42)
        signal = np.random.randn(500)
        n_surrogates = 100
        
        surrogates = generate_phase_shuffled_surrogates(signal, n_surrogates)
        
        assert len(surrogates) == n_surrogates

    def test_all_surrogates_valid(self):
        """Verify all generated surrogates are valid signals."""
        set_seed(42)
        signal = np.random.randn(500)
        n_surrogates = 50
        
        surrogates = generate_phase_shuffled_surrogates(signal, n_surrogates)
        
        for surrogate in surrogates:
            assert isinstance(surrogate, np.ndarray)
            assert surrogate.shape == signal.shape
            assert not np.any(np.isnan(surrogate))
            assert not np.any(np.isinf(surrogate))

    def test_surrogates_are_different(self):
        """Verify that different surrogates are not identical."""
        set_seed(42)
        signal = np.random.randn(500)
        n_surrogates = 10
        
        surrogates = generate_phase_shuffled_surrogates(signal, n_surrogates)
        
        # Check pairwise differences
        for i in range(n_surrogates):
            for j in range(i + 1, n_surrogates):
                assert not np.array_equal(surrogates[i], surrogates[j]), \
                    f"Surrogates {i} and {j} are identical"

class TestComputeSurrogateVariability:
    """Tests for computing variability metrics from surrogates."""

    def test_returns_mean_and_std(self):
        """Verify function returns mean and std of surrogate metrics."""
        set_seed(42)
        # Create simple surrogate metrics (just values)
        surrogate_metrics = np.random.randn(100)
        
        mean_val, std_val = compute_surrogate_variability(surrogate_metrics)
        
        np.testing.assert_almost_equal(mean_val, np.mean(surrogate_metrics))
        np.testing.assert_almost_equal(std_val, np.std(surrogate_metrics))

    def test_handles_small_sample(self):
        """Test with small number of surrogates."""
        set_seed(42)
        surrogate_metrics = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        mean_val, std_val = compute_surrogate_variability(surrogate_metrics)
        
        assert mean_val == 3.0
        assert std_val == np.std(surrogate_metrics)

class TestValidateMetricSignificance:
    """Tests for validating metric significance against null model."""

    def test_p_value_calculation(self):
        """Verify p-value is calculated correctly."""
        set_seed(42)
        # Create surrogate distribution centered at 0
        surrogate_metrics = np.random.randn(1000) * 0.1
        observed_metric = 0.5  # Far from the surrogate mean
        
        p_value = validate_metric_significance(observed_metric, surrogate_metrics)
        
        # P-value should be very small for such an extreme value
        assert p_value < 0.01

    def test_p_value_when_observed_is_low(self):
        """Verify p-value calculation when observed is within distribution."""
        set_seed(42)
        surrogate_metrics = np.random.randn(1000)
        observed_metric = 0.0  # Near the mean of the surrogate distribution
        
        p_value = validate_metric_significance(observed_metric, surrogate_metrics)
        
        # P-value should be large (not significant)
        assert p_value > 0.1

    def test_p_value_bounds(self):
        """Verify p-value is always between 0 and 1."""
        set_seed(42)
        surrogate_metrics = np.random.randn(1000)
        
        for observed in [-10, -1, 0, 1, 10]:
            p_value = validate_metric_significance(observed, surrogate_metrics)
            assert 0.0 <= p_value <= 1.0

    def test_two_tailed_test(self):
        """Verify two-tailed p-value calculation."""
        set_seed(42)
        surrogate_metrics = np.random.randn(1000)
        observed_positive = np.mean(surrogate_metrics) + 3 * np.std(surrogate_metrics)
        observed_negative = np.mean(surrogate_metrics) - 3 * np.std(surrogate_metrics)
        
        p_positive = validate_metric_significance(observed_positive, surrogate_metrics)
        p_negative = validate_metric_significance(observed_negative, surrogate_metrics)
        
        # Both should be small (significant)
        assert p_positive < 0.01
        assert p_negative < 0.01

    def test_with_empty_surrogates(self):
        """Test behavior with empty surrogate list (should raise error)."""
        with pytest.raises(ValueError):
            validate_metric_significance(0.5, np.array([]))

class TestIntegration:
    """Integration tests combining multiple null model functions."""

    def test_full_pipeline(self):
        """Test the full null model validation pipeline."""
        set_seed(42)
        
        # Simulate a time series (e.g., connectivity time series)
        n_timepoints = 1000
        signal = np.random.randn(n_timepoints)
        
        # Generate surrogates
        n_surrogates = 100
        surrogates = generate_phase_shuffled_surrogates(signal, n_surrogates)
        
        # Compute a simple metric for each (e.g., variance)
        observed_metric = np.var(signal)
        surrogate_metrics = [np.var(s) for s in surrogates]
        surrogate_metrics = np.array(surrogate_metrics)
        
        # Validate significance
        p_value = validate_metric_significance(observed_metric, surrogate_metrics)
        
        # P-value should be valid
        assert 0.0 <= p_value <= 1.0

    def test_with_realistic_connectivity_pattern(self):
        """Test with a signal that has realistic connectivity patterns."""
        set_seed(42)
        
        # Create a signal with some autocorrelation (like fMRI time series)
        n_timepoints = 1000
        noise = np.random.randn(n_timepoints)
        signal = np.zeros(n_timepoints)
        for i in range(n_timepoints):
            if i == 0:
                signal[i] = noise[i]
            else:
                signal[i] = 0.5 * signal[i-1] + 0.5 * noise[i]  # AR(1) process
        
        # Generate surrogates
        n_surrogates = 50
        surrogates = generate_phase_shuffled_surrogates(signal, n_surrogates)
        
        # Compute autocorrelation as the metric
        def autocorr(x):
            result = np.correlate(x - np.mean(x), x - np.mean(x), mode='full')
            return result[result.size // 2] / (len(x) * np.var(x))
        
        observed_metric = autocorr(signal)
        surrogate_metrics = np.array([autocorr(s) for s in surrogates])
        
        # Validate
        p_value = validate_metric_significance(observed_metric, surrogate_metrics)
        
        # The original signal should have higher autocorrelation than shuffled
        assert p_value < 0.05, "Autocorrelation should be significantly higher in original"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])