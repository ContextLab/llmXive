"""
Unit tests for preprocessing functions in code/preprocess.py.
Specifically tests bandpass filter attenuation as per T007 requirements.
"""
import numpy as np
import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocess import apply_bandpass_filter, load_config
import mne


class TestBandpassFilterAttenuation:
    """Tests for the 1-40 Hz bandpass filter attenuation."""

    def test_filter_attenuates_50hz_line_noise(self):
        """
        Verify that a 50Hz line noise peak is attenuated by >20dB in the output spectrum.
        
        This test creates a synthetic signal containing:
        1. A 10 Hz component (passband)
        2. A 50 Hz component (stopband - line noise)
        
        After filtering, the 50Hz component should be significantly reduced (>20dB).
        """
        # Configuration
        sfreq = 256.0  # Sampling frequency
        duration = 10.0  # seconds
        t = np.arange(0, duration, 1/sfreq)
        
        # Create synthetic signal: 10 Hz (pass) + 50 Hz (stop)
        # Amplitude of 50Hz is set higher to ensure we can measure attenuation clearly
        signal_10hz = 1.0 * np.sin(2 * np.pi * 10 * t)
        signal_50hz = 1.0 * np.sin(2 * np.pi * 50 * t)
        raw_signal = signal_10hz + signal_50hz
        
        # Create MNE RawArray (single channel)
        info = mne.create_info(ch_names=['EEG_001'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(raw_signal.reshape(1, -1), info)
        
        # Load config to get filter parameters
        config = load_config()
        l_freq = config.get('filter', {}).get('l_freq', 1.0)
        h_freq = config.get('filter', {}).get('h_freq', 40.0)
        
        # Apply bandpass filter
        filtered_raw = apply_bandpass_filter(raw, l_freq=l_freq, h_freq=h_freq)
        
        # Get data for analysis
        original_data = raw.get_data()[0]
        filtered_data = filtered_raw.get_data()[0]
        
        # Compute FFT to analyze frequency components
        n = len(original_data)
        freqs = np.fft.rfftfreq(n, 1/sfreq)
        
        # Compute power spectral density (magnitude squared)
        original_fft = np.fft.rfft(original_data)
        filtered_fft = np.fft.rfft(filtered_data)
        
        original_power = np.abs(original_fft) ** 2
        filtered_power = np.abs(filtered_fft) ** 2
        
        # Find indices for 10 Hz and 50 Hz
        idx_10hz = np.argmin(np.abs(freqs - 10))
        idx_50hz = np.argmin(np.abs(freqs - 50))
        
        # Calculate power at 10 Hz and 50 Hz
        power_10hz_original = original_power[idx_10hz]
        power_10hz_filtered = filtered_power[idx_10hz]
        
        power_50hz_original = original_power[idx_50hz]
        power_50hz_filtered = filtered_power[idx_50hz]
        
        # Convert to dB
        # dB = 10 * log10(P_filtered / P_original)
        # For attenuation, we expect negative values
        attenuation_10hz = 10 * np.log10(power_10hz_filtered / (power_10hz_original + 1e-10))
        attenuation_50hz = 10 * np.log10(power_50hz_filtered / (power_50hz_original + 1e-10))
        
        # Assertions
        # 1. 10 Hz component should be preserved (attenuation > -3dB, i.e., less than 3dB loss)
        assert attenuation_10hz > -3.0, f"Passband signal (10Hz) attenuated too much: {attenuation_10hz:.2f} dB"
        
        # 2. 50 Hz component should be attenuated by >20dB
        assert attenuation_50hz < -20.0, (
            f"Stopband signal (50Hz) not sufficiently attenuated: {attenuation_50hz:.2f} dB. "
            f"Expected < -20.0 dB attenuation."
        )
        
        print(f"Test Results:")
        print(f"  10 Hz (Passband) Attenuation: {attenuation_10hz:.2f} dB")
        print(f"  50 Hz (Stopband) Attenuation: {attenuation_50hz:.2f} dB")
        print(f"  Filter cutoffs used: {l_freq} Hz - {h_freq} Hz")

    def test_filter_parameters_from_config(self):
        """Verify that filter uses parameters from config.yaml."""
        config = load_config()
        
        # Check that filter section exists
        assert 'filter' in config, "Config must contain 'filter' section"
        assert 'l_freq' in config['filter'], "Config must specify 'l_freq'"
        assert 'h_freq' in config['filter'], "Config must specify 'h_freq'"
        
        # Verify they are within expected ranges per task requirements
        l_freq = config['filter']['l_freq']
        h_freq = config['filter']['h_freq']
        
        assert 0.5 <= l_freq <= 2.0, f"Low cutoff {l_freq} Hz outside expected 0.5-2.0 Hz range"
        assert 35.0 <= h_freq <= 45.0, f"High cutoff {h_freq} Hz outside expected 35-45 Hz range"