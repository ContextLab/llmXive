import pytest
import numpy as np
from scipy import signal
import os
import sys
import tempfile

# Import the specific function we need to test from the existing API
from src.downsample import design_fir_filter, calculate_frequency_response, downsample_with_correction

class TestAntiAliasing:
    """
    Unit test for T010: Verify FFT spectral content to ensure anti-aliasing
    artifacts are suppressed relative to the signal peak and Nyquist limits
    are respected during downsampling.
    """

    def test_downsample_anti_aliasing(self):
        """
        Verify that downsampling with the FIR filter suppresses aliasing artifacts.
        
        Methodology:
        1. Generate a test signal containing frequencies above and below the 
           target Nyquist limit.
        2. Downsample the signal using the implemented FIR filter.
        3. Perform FFT on the downsampled signal.
        4. Verify that frequency components above the new Nyquist limit are 
           suppressed to negligible levels (e.g., >40dB below the signal peak).
        """
        # Parameters
        fs_original = 4096  # Original sampling rate
        fs_target = 512     # Target sampling rate (Nyquist = 256 Hz)
        duration = 1.0      # 1 second
        
        # Create a test signal:
        # - A strong component at 100 Hz (below new Nyquist)
        # - A strong component at 300 Hz (above new Nyquist, should be aliased/filtered)
        # - A strong component at 1500 Hz (well above new Nyquist)
        t = np.arange(0, duration, 1/fs_original)
        
        # Signal components
        f_signal = 100.0
        f_alias_target = 300.0  # Should be removed by filter
        f_alias_high = 1500.0   # Should be removed by filter
        
        amplitude = 1.0
        noise_amplitude = 0.01
        
        # Generate signal
        x = (amplitude * np.sin(2 * np.pi * f_signal * t) +
             amplitude * np.sin(2 * np.pi * f_alias_target * t) +
             amplitude * np.sin(2 * np.pi * f_alias_high * t) +
             noise_amplitude * np.random.randn(len(t)))
        
        # Design the FIR filter
        # Cutoff frequency is set to just below the target Nyquist (fs_target / 2)
        # We use a safety margin to ensure strong attenuation
        cutoff = (fs_target / 2) * 0.95
        numtaps = 101  # Filter length (must be odd for type I)
        
        # Create the filter
        b, a = design_fir_filter(fs_original, cutoff, numtaps)
        
        # Apply filter and downsample
        # We'll use a simple decimation approach here for testing, 
        # assuming the downsample_with_correction function handles the filtering
        # For this specific test, we'll manually filter and decimate to isolate
        # the anti-aliasing behavior
        
        # Filter the signal
        x_filtered = signal.filtfilt(b, a, x)
        
        # Calculate decimation factor
        decimation_factor = fs_original // fs_target
        
        # Decimate (take every Nth sample)
        x_downsampled = x_filtered[::decimation_factor]
        
        # Perform FFT on the downsampled signal
        N = len(x_downsampled)
        yf = np.fft.fft(x_downsampled)
        xf = np.fft.fftfreq(N, 1/fs_target)[:N//2]
        magnitude = 2.0/N * np.abs(yf[0:N//2])
        
        # Find the peak magnitude (should be at 100 Hz)
        peak_idx = np.argmax(magnitude)
        peak_freq = xf[peak_idx]
        peak_magnitude = magnitude[peak_idx]
        
        # Define the Nyquist limit for the downsampled signal
        nyquist_limit = fs_target / 2
        
        # Check that the peak is within the valid frequency range
        assert peak_freq < nyquist_limit, f"Peak frequency {peak_freq} Hz exceeds Nyquist limit {nyquist_limit} Hz"
        
        # Check for aliasing artifacts
        # Look for significant energy above the Nyquist limit (should be near zero)
        # In the FFT, frequencies above Nyquist are folded back, so we check
        # if there's significant energy near the Nyquist frequency that shouldn't be there
        
        # Calculate the noise floor (median of magnitude spectrum excluding the peak region)
        peak_region = (xf > peak_freq - 20) & (xf < peak_freq + 20)
        noise_floor = np.median(magnitude[~peak_region])
        
        # Define a threshold for "negligible" (e.g., 40 dB below peak)
        # 40 dB = factor of 100 in amplitude
        threshold = peak_magnitude / 100.0
        
        # Check that no significant energy exists above the threshold outside the peak region
        # This verifies that aliasing artifacts are suppressed
        significant_energy_indices = np.where((magnitude > threshold) & (~peak_region))[0]
        
        # If there are significant energy indices, check if they are near the Nyquist limit
        # (which would indicate aliasing)
        if len(significant_energy_indices) > 0:
            # Check if any of these are near the Nyquist limit
            near_nyquist = np.abs(xf[significant_energy_indices] - nyquist_limit) < 20
            if np.any(near_nyquist):
                # This might indicate some aliasing, but we need to check the magnitude
                # relative to the noise floor
                max_alias_magnitude = np.max(magnitude[significant_energy_indices])
                alias_to_noise_ratio = max_alias_magnitude / noise_floor
                
                # If the alias is only slightly above the noise floor, it's acceptable
                # We allow some residual energy as long as it's not a strong artifact
                assert alias_to_noise_ratio < 10, (
                    f"Significant aliasing detected: alias magnitude {max_alias_magnitude:.4f} "
                    f"is {alias_to_noise_ratio:.2f}x above noise floor {noise_floor:.4f}. "
                    f"Expected suppression > 40dB relative to signal peak."
                )
        
        # Verify that the signal component at 100 Hz is preserved
        # (within 10% amplitude tolerance)
        expected_100hz_idx = np.argmin(np.abs(xf - f_signal))
        measured_100hz_magnitude = magnitude[expected_100hz_idx]
        
        # Allow for some filter attenuation (we'll check relative to the peak)
        # The 100 Hz component should be the dominant one
        assert measured_100hz_magnitude > peak_magnitude * 0.8, (
            f"Signal component at {f_signal} Hz not properly preserved. "
            f"Expected > 80% of peak magnitude, got {measured_100hz_magnitude/peak_magnitude*100:.1f}%"
        )
        
        # Additional check: verify that the frequency response of the filter
        # shows strong attenuation at frequencies above the cutoff
        w, h = signal.freqz(b, a, worN=8000)
        freqs_hz = w * fs_original / (2 * np.pi)
        
        # Find attenuation at 300 Hz (should be > 40 dB)
        idx_300hz = np.argmin(np.abs(freqs_hz - 300))
        attenuation_300hz = -20 * np.log10(np.abs(h[idx_300hz]))
        
        # Find attenuation at 1500 Hz (should be > 40 dB)
        idx_1500hz = np.argmin(np.abs(freqs_hz - 1500))
        attenuation_1500hz = -20 * np.log10(np.abs(h[idx_1500hz]))
        
        # Assert that the filter provides sufficient attenuation
        assert attenuation_300hz > 40, (
            f"Filter attenuation at 300 Hz is only {attenuation_300hz:.2f} dB. "
            f"Expected > 40 dB to prevent aliasing."
        )
        
        assert attenuation_1500hz > 40, (
            f"Filter attenuation at 1500 Hz is only {attenuation_1500hz:.2f} dB. "
            f"Expected > 40 dB to prevent aliasing."
        )