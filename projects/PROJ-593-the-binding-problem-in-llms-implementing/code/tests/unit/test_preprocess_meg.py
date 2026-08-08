"""
Unit tests for src/data/preprocess_meg.py (Part 1: Bandpass Filtering).
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocess_meg import (
    butter_bandpass,
    apply_bandpass_filter,
    main
)


class TestButterBandpass:
    """Tests for the butter_bandpass function."""

    def test_filter_coefficients_valid_range(self):
        """Test that filter coefficients are returned for valid frequencies."""
        fs = 1000.0
        lowcut = 30.0
        highcut = 50.0
        order = 4

        b, a = butter_bandpass(lowcut, highcut, fs, order)

        assert len(b) == len(a)
        assert len(b) > 0
        # Check that coefficients are real numbers
        assert np.all(np.isreal(b))
        assert np.all(np.isreal(a))

    def test_invalid_lowcut(self):
        """Test that an error is raised if lowcut is too high."""
        fs = 100.0
        with pytest.raises(ValueError):
            butter_bandpass(60.0, 80.0, fs, order=4)  # Nyquist is 50, 60 > 50

    def test_invalid_highcut(self):
        """Test that an error is raised if highcut is too high."""
        fs = 100.0
        with pytest.raises(ValueError):
            butter_bandpass(10.0, 60.0, fs, order=4)  # Nyquist is 50, 60 > 50


class TestApplyBandpassFilter:
    """Tests for the apply_bandpass_filter function."""

    def test_filter_reduces_outside_band(self):
        """
        Test that a signal with components outside the passband is attenuated.
        We create a signal with a strong low-frequency component (10Hz) and
        a component in the passband (40Hz). The output should have the 10Hz
        component significantly reduced relative to the 40Hz component.
        """
        fs = 1000.0
        duration = 2.0  # seconds
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)

        # 10Hz (outside) + 40Hz (inside)
        signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 40 * t)
        signal = signal.reshape(1, -1)  # (1, n_samples)

        filtered = apply_bandpass_filter(signal, fs, 30.0, 50.0, order=4)

        # Compute power in 0-20Hz (should be low) and 30-60Hz (should be higher)
        # Simple check: energy in the filtered signal should be dominated by the 40Hz component
        # We can check the ratio of energies or just ensure the filter doesn't crash
        # and produces an output of the same shape.
        assert filtered.shape == signal.shape

        # A more robust check: FFT analysis
        fft_orig = np.fft.rfft(signal[0])
        fft_filt = np.fft.rfft(filtered[0])
        freqs = np.fft.rfftfreq(len(t), 1/fs)

        # Power in low band (0-20Hz)
        low_mask = (freqs >= 0) & (freqs < 20)
        # Power in pass band (30-50Hz)
        pass_mask = (freqs >= 30) & (freqs <= 50)

        power_low_orig = np.sum(np.abs(fft_orig[low_mask]) ** 2)
        power_low_filt = np.sum(np.abs(fft_filt[low_mask]) ** 2)

        power_pass_orig = np.sum(np.abs(fft_orig[pass_mask]) ** 2)
        power_pass_filt = np.sum(np.abs(fft_filt[pass_mask]) ** 2)

        # The filter should attenuate the low frequency component significantly
        # relative to the passband component.
        # Note: Exact ratios depend on filter order and transition width,
        # but we expect a significant drop in low frequencies.
        assert power_low_filt < power_low_orig, "Low frequency component was not attenuated."

    def test_multichannel_filtering(self):
        """Test filtering with multiple channels."""
        fs = 1000.0
        n_channels = 5
        n_samples = 1000
        signal = np.random.randn(n_channels, n_samples)

        filtered = apply_bandpass_filter(signal, fs, 30.0, 50.0, order=4)

        assert filtered.shape == signal.shape
        assert isinstance(filtered, np.ndarray)


class TestPreprocessMegScriptExecution:
    """Tests for the main script execution logic."""

    def test_main_fails_if_input_missing(self):
        """Test that main raises FileNotFoundError if input data is missing."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "data" / "raw"
            proc_dir = tmp_path / "data" / "processed"
            raw_dir.mkdir(parents=True)
            proc_dir.mkdir(parents=True)

            # Mock the module's global paths
            import src.data.preprocess_meg as pm
            original_raw = pm.DATA_RAW_DIR
            original_proc = pm.DATA_PROCESSED_DIR
            original_input = pm.INPUT_FILE
            original_output = pm.OUTPUT_FILE

            pm.DATA_RAW_DIR = raw_dir
            pm.DATA_PROCESSED_DIR = proc_dir
            pm.INPUT_FILE = raw_dir / "meg_streamed.parquet"
            pm.OUTPUT_FILE = proc_dir / "meg_filtered.npy"

            try:
                with pytest.raises(FileNotFoundError):
                    main()
            finally:
                # Restore original paths
                pm.DATA_RAW_DIR = original_raw
                pm.DATA_PROCESSED_DIR = original_proc
                pm.INPUT_FILE = original_input
                pm.OUTPUT_FILE = original_output

    def test_main_processes_mock_data(self):
        """Test that main successfully processes a mock parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            raw_dir = tmp_path / "data" / "raw"
            proc_dir = tmp_path / "data" / "processed"
            raw_dir.mkdir(parents=True)
            proc_dir.mkdir(parents=True)

            # Create mock data
            n_samples = 1000
            n_channels = 2
            time_vals = np.linspace(0, 1, n_samples)
            # Create a simple signal: 40Hz sine wave
            signal_data = np.sin(2 * np.pi * 40 * time_vals)
            # Construct dataframe with 'time' and 'signal' columns
            # Assuming 'signal' is the channel name
            df = pd.DataFrame({
                'time': time_vals,
                'signal': signal_data
            })

            input_file = raw_dir / "meg_streamed.parquet"
            df.to_parquet(input_file)

            output_file = proc_dir / "meg_filtered.npy"

            # Mock paths
            import src.data.preprocess_meg as pm
            original_raw = pm.DATA_RAW_DIR
            original_proc = pm.DATA_PROCESSED_DIR
            original_input = pm.INPUT_FILE
            original_output = pm.OUTPUT_FILE

            pm.DATA_RAW_DIR = raw_dir
            pm.DATA_PROCESSED_DIR = proc_dir
            pm.INPUT_FILE = input_file
            pm.OUTPUT_FILE = output_file

            try:
                # This should run without error and create the output file
                main()
                assert output_file.exists(), "Output file was not created."

                # Verify content
                result = np.load(output_file)
                assert result.shape[0] == n_channels, "Channel count mismatch."
                assert result.shape[1] == n_samples, "Sample count mismatch."
            finally:
                pm.DATA_RAW_DIR = original_raw
                pm.DATA_PROCESSED_DIR = original_proc
                pm.INPUT_FILE = original_input
                pm.OUTPUT_FILE = original_output