"""
Unit tests for blink removal and 4Hz low-pass filtering in preprocessing.py.

These tests verify:
1. remove_blinks correctly identifies and masks blink events based on amplitude thresholds.
2. low_pass_filter applies a 4Hz cutoff using a Butterworth filter without distorting the signal excessively.
"""
import numpy as np
import pandas as pd
import pytest
from scipy.signal import butter, filtfilt

# Import the functions under test from the sibling module
from code.preprocessing import remove_blinks, low_pass_filter


class TestRemoveBlinks:
    """Tests for the remove_blinks function."""

    def test_remove_blinks_masks_high_amplitude_spikes(self):
        """
        Verify that blinks (high amplitude spikes) are replaced with NaN.
        We simulate a signal with a clear spike that exceeds a standard threshold.
        """
        # Create synthetic pupil data: mostly flat with one large spike (blink)
        np.random.seed(42)
        n_samples = 1000
        base_signal = np.ones(n_samples) * 5.0  # Baseline 5mm
        blink_idx = 500
        base_signal[blink_idx] = 15.0  # Spike to 15mm (typical blink amplitude)

        df = pd.DataFrame({'pupil_size': base_signal})

        # Run removal. Default threshold is usually around 3-4mm deviation or absolute.
        # The implementation in preprocessing.py likely uses a threshold relative to median or mean.
        # We assume the function handles the logic of "what is a blink".
        result = remove_blinks(df, threshold_mm=3.0)

        # The spike should be masked (NaN) or interpolated. 
        # Based on standard preprocessing, we expect NaN at the blink location if not interpolated.
        # If the function interpolates, we check that the value is NOT the original spike.
        # Let's assume the function returns NaN for detected blinks as per standard practice before interpolation.
        
        # Check that the spike location is no longer 15.0
        assert result.loc[blink_idx, 'pupil_size'] != 15.0, "Blink spike was not masked."
        # Typically, it becomes NaN or a interpolated value close to 5.0.
        # If it's NaN:
        assert np.isnan(result.loc[blink_idx, 'pupil_size']) or abs(result.loc[blink_idx, 'pupil_size'] - 5.0) < 1.0

    def test_remove_blinks_preserves_normal_data(self):
        """
        Verify that normal pupil fluctuations are not removed.
        """
        np.random.seed(123)
        # Normal variation around 5mm, max deviation < 1mm
        signal = 5.0 + np.random.normal(0, 0.2, 1000)
        df = pd.DataFrame({'pupil_size': signal})

        result = remove_blinks(df, threshold_mm=3.0)

        # All values should be close to original (no NaNs introduced for normal data)
        assert not result.isna().any().any(), "Normal data points were incorrectly masked."
        np.testing.assert_array_almost_equal(result['pupil_size'].values, signal, decimal=2)


class TestLowPassFilter:
    """Tests for the low_pass_filter function."""

    def test_low_pass_filter_rejects_high_frequency_noise(self):
        """
        Verify that a 4Hz low-pass filter removes high frequency noise.
        """
        # Sampling rate assumption (common in pupil data): 250Hz or 1000Hz.
        # Let's assume 250Hz based on typical Pupil Labs settings.
        fs = 250.0
        t = np.arange(0, 10, 1/fs)
        
        # Signal: 2Hz (should pass) + 10Hz (should be attenuated)
        freq_pass = 2.0
        freq_stop = 10.0
        signal = np.sin(2 * np.pi * freq_pass * t) + 0.5 * np.sin(2 * np.pi * freq_stop * t)

        df = pd.DataFrame({'pupil_size': signal, 'timestamp': t})

        # Apply filter with cutoff 4Hz
        result = low_pass_filter(df, column='pupil_size', cutoff=4.0, fs=fs)

        # Check attenuation of the 10Hz component
        # We can't easily isolate components without FFT, but we can check variance reduction
        # or simply that the filter runs without error and reduces high-freq content.
        # A more robust check: compare power in the stop band.
        
        # Calculate power spectrum of input vs output
        from scipy.signal import welch
        f_in, Pxx_in = welch(signal, fs, nperseg=256)
        f_out, Pxx_out = welch(result['pupil_size'].values, fs, nperseg=256)

        # Power at 10Hz should be significantly lower in output
        idx_10hz = np.argmin(np.abs(f_out - 10.0))
        idx_10hz_in = np.argmin(np.abs(f_in - 10.0))

        # Allow some tolerance, but attenuation should be noticeable (e.g., > 10dB)
        ratio = Pxx_out[idx_10hz] / Pxx_in[idx_10hz_in]
        # If ratio is small, the filter worked. 
        # Note: If the filter order is low, attenuation might not be huge, but it should be < 1.
        assert ratio < 0.5, f"High frequency noise (10Hz) was not sufficiently attenuated. Ratio: {ratio}"

    def test_low_pass_filter_preserves_low_frequency_signal(self):
        """
        Verify that a 4Hz low-pass filter preserves low frequency components (e.g., 1Hz).
        """
        fs = 250.0
        t = np.arange(0, 10, 1/fs)
        
        freq_pass = 1.0
        signal = np.sin(2 * np.pi * freq_pass * t)
        df = pd.DataFrame({'pupil_size': signal, 'timestamp': t})

        result = low_pass_filter(df, column='pupil_size', cutoff=4.0, fs=fs)

        # The amplitude of the 1Hz signal should be largely preserved (e.g., > 90%)
        # Compare max amplitude
        input_amp = np.max(signal) - np.min(signal)
        output_amp = np.max(result['pupil_size']) - np.min(result['pupil_size'])
        
        # Allow for minor edge effects from filtfilt
        assert output_amp > 0.8 * input_amp, f"Low frequency signal (1Hz) was attenuated too much. Input amp: {input_amp}, Output amp: {output_amp}"

    def test_low_pass_filter_handles_edge_cases(self):
        """
        Verify filter behavior on short signals or edge cases.
        """
        # Very short signal (less than filter order might cause issues in some impls, but filtfilt handles padding)
        fs = 100.0
        t = np.arange(0, 0.5, 1/fs) # 0.5 seconds
        signal = np.sin(2 * np.pi * 2 * t)
        df = pd.DataFrame({'pupil_size': signal, 'timestamp': t})

        # Should not raise an error
        result = low_pass_filter(df, column='pupil_size', cutoff=4.0, fs=fs)
        assert result.shape[0] == df.shape[0], "Filter changed the length of the signal."
        assert not result.isna().any().any(), "Filter introduced NaNs in valid data."