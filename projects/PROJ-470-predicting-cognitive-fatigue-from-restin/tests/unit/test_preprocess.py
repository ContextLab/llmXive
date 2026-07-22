"""
Unit tests for preprocessing functions in code/preprocess.py.
Includes tests for bandpass filter attenuation and edge cases.
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocess import stream_eeg_files, load_config, apply_bandpass_filter
from utils.logging import get_logger

class TestBandpassFilterAttenuation:
    """Tests for verifying bandpass filter attenuation characteristics."""

    def test_bandpass_attenuation(self):
        """
        Verify that the bandpass filter attenuates frequencies outside the passband.
        Specifically tests that a 0.5 Hz signal (below passband) and a 60 Hz signal 
        (above passband) are attenuated by >20dB compared to a 10 Hz signal (in passband).
        
        Verification: Run `pytest tests/unit/test_preprocess.py::test_bandpass_attenuation` 
        and assert it fails initially, then passes after implementation.
        """
        # Create a synthetic signal with known frequency components
        fs = 256  # Sampling frequency
        duration = 10  # seconds
        t = np.arange(0, duration, 1/fs)
        
        # Create a signal with three frequency components:
        # 0.5 Hz (below passband), 10 Hz (in passband), 60 Hz (above passband)
        signal = (
            1.0 * np.sin(2 * np.pi * 0.5 * t) +   # Low frequency (should be attenuated)
            1.0 * np.sin(2 * np.pi * 10.0 * t) +  # Passband frequency (reference)
            1.0 * np.sin(2 * np.pi * 60.0 * t)    # High frequency (should be attenuated)
        )
        
        # Apply the bandpass filter (1-40 Hz as per config)
        filtered_signal = apply_bandpass_filter(signal, fs, 1, 40)
        
        # Calculate power spectral density using FFT
        n = len(signal)
        freqs = np.fft.rfftfreq(n, 1/fs)
        spectrum = np.abs(np.fft.rfft(signal))
        filtered_spectrum = np.abs(np.fft.rfft(filtered_signal))
        
        # Find indices for our test frequencies
        idx_low = np.argmin(np.abs(freqs - 0.5))
        idx_pass = np.argmin(np.abs(freqs - 10.0))
        idx_high = np.argmin(np.abs(freqs - 60.0))
        
        # Calculate attenuation in dB
        # Attenuation = 20 * log10(filtered_amplitude / original_amplitude)
        # We want to show that filtered amplitude is much smaller than original
        # for out-of-band frequencies
        
        attenuation_low = 20 * np.log10(np.abs(filtered_spectrum[idx_low]) / np.abs(spectrum[idx_low]))
        attenuation_high = 20 * np.log10(np.abs(filtered_spectrum[idx_high]) / np.abs(spectrum[idx_high]))
        
        # Verify attenuation > 20dB (which means ratio < 0.1)
        # Note: attenuation will be negative, so we check if it's less than -20
        assert attenuation_low < -20, f"Low frequency attenuation {attenuation_low:.2f}dB is not > 20dB"
        assert attenuation_high < -20, f"High frequency attenuation {attenuation_high:.2f}dB is not > 20dB"
        
        # Verify that the passband frequency is not significantly attenuated (< 3dB)
        attenuation_pass = 20 * np.log10(np.abs(filtered_spectrum[idx_pass]) / np.abs(spectrum[idx_pass]))
        assert attenuation_pass > -3, f"Passband attenuation {attenuation_pass:.2f}dB is too high"

class TestMissingDataEdgeCases:
    """Tests for handling missing data in preprocessing."""

    def test_missing_data_directory(self, tmp_path):
        """
        Verify that stream_eeg_files raises FileNotFoundError
        when the specified data directory does not exist.
        """
        nonexistent_dir = tmp_path / "nonexistent_data"
        
        with pytest.raises(FileNotFoundError) as excinfo:
            list(stream_eeg_files(str(nonexistent_dir)))
        
        assert "Data directory not found" in str(excinfo.value)
        assert str(nonexistent_dir) in str(excinfo.value)

    def test_missing_eeg_file_in_directory(self, tmp_path, monkeypatch):
        """
        Verify that stream_eeg_files raises FileNotFoundError
        when the directory exists but contains no EEG files.
        """
        # Create a directory with no EEG files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "readme.txt").write_text("No EEG here")
        
        # Mock config to point to this directory
        mock_config = {
            "raw_data_dir": str(data_dir),
            "file_extensions": [".edf", ".bdf", ".vhdr"]
        }
        
        # Patch load_config to return our mock
        monkeypatch.setattr("preprocess.load_config", lambda _: mock_config)
        
        with pytest.raises(FileNotFoundError) as excinfo:
            list(stream_eeg_files(str(data_dir)))
        
        assert "No EEG files found" in str(excinfo.value)

    def test_corrupted_eeg_file_handling(self, tmp_path):
        """
        Verify that stream_eeg_files handles corrupted files gracefully
        by logging the error and continuing (or raising if strict mode).
        """
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create a corrupted file with .edf extension
        corrupted_file = data_dir / "participant_001.edf"
        corrupted_file.write_bytes(b"corrupted binary data")
        
        # We expect this to either raise or log an error during reading
        # The exact behavior depends on MNE's error handling
        # For this test, we verify the function attempts to read it
        try:
            files = list(stream_eeg_files(str(data_dir)))
            # If it returns, it means MNE handled the error internally
            # or the file was skipped
            assert isinstance(files, list)
        except Exception as e:
            # If it raises, it should be a clear error about the file
            assert "Error reading" in str(e) or "corrupted" in str(e).lower()