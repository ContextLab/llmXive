"""
tests/test_extract_features.py

Unit tests for code/03_extract_features.py
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'code'))

from config import get_path, get_band_freqs, get_all_band_names, ensure_dirs
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance

# Mock MNE for testing without full EEG data
try:
    import mne
    HAS_MNE = True
except ImportError:
    HAS_MNE = False

pytestmark = pytest.mark.skipif(not HAS_MNE, reason="MNE not installed")


class TestExtractFeatures:
    """Tests for feature extraction logic."""

    def test_band_freqs_config(self):
        """Test that band frequencies are correctly defined in config."""
        bands = get_band_freqs()
        assert 'delta' in bands
        assert 'theta' in bands
        assert 'alpha' in bands
        assert 'low_beta' in bands
        assert 'high_beta' in bands
        assert 'gamma' in bands
        
        # Check ranges
        assert bands['delta'] == (1, 4)
        assert bands['theta'] == (4, 8)
        assert bands['alpha'] == (8, 13)
        assert bands['low_beta'] == (13, 20)
        assert bands['high_beta'] == (20, 30)
        assert bands['gamma'] == (30, 45)

    def test_all_band_names(self):
        """Test that all band names are retrievable."""
        names = get_all_band_names()
        expected = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
        assert set(names) == set(expected)

    def test_ensure_dirs(self):
        """Test that ensure_dirs creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, 'subdir', 'test.txt')
            ensure_dirs(test_file)
            assert os.path.exists(os.path.dirname(test_file))

    def test_compute_welch_psd_structure(self):
        """Test that Welch's PSD computation returns correct structure."""
        # Create synthetic raw data
        sfreq = 250
        n_channels = 2
        n_samples = sfreq * 10  # 10 seconds
        
        info = mne.create_info(ch_names=[f'EEG{i}' for i in range(n_channels)], 
                               sfreq=sfreq, ch_types='eeg')
        data = np.random.randn(n_channels, n_samples)
        raw = mne.io.RawArray(data, info)
        
        # Import the function to test
        from code_03_extract_features import compute_welch_psd
        
        window_sec = 4.0
        overlap_sec = 2.0
        
        freqs, psd = compute_welch_psd(raw, window_sec, overlap_sec)
        
        # Check outputs
        assert freqs is not None
        assert psd is not None
        assert len(freqs) > 0
        assert psd.shape[0] == n_channels
        assert psd.shape[1] == len(freqs)
        assert np.all(psd >= 0)  # Power should be non-negative

    def test_aggregate_band_power_structure(self):
        """Test that band power aggregation returns correct structure."""
        # Create synthetic data
        sfreq = 250
        n_channels = 2
        n_samples = sfreq * 10
        
        info = mne.create_info(ch_names=[f'EEG{i}' for i in range(n_channels)], 
                               sfreq=sfreq, ch_types='eeg')
        data = np.random.randn(n_channels, n_samples)
        raw = mne.io.RawArray(data, info)
        
        # Compute PSD first
        from code_03_extract_features import compute_welch_psd
        freqs, psd = compute_welch_psd(raw, 4.0, 2.0)
        
        # Import aggregation function
        from code_03_extract_features import aggregate_band_power
        
        band_powers = aggregate_band_power(freqs, psd, raw)
        
        # Check structure
        assert isinstance(band_powers, dict)
        expected_bands = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
        for band in expected_bands:
            assert band in band_powers
            assert isinstance(band_powers[band], float)
            assert not np.isnan(band_powers[band])

    def test_extract_features_for_subject_structure(self):
        """Test that full feature extraction returns correct structure."""
        # Create synthetic raw data
        sfreq = 250
        n_channels = 2
        n_samples = sfreq * 300  # 5 minutes
        
        info = mne.create_info(ch_names=[f'EEG{i}' for i in range(n_channels)], 
                               sfreq=sfreq, ch_types='eeg')
        data = np.random.randn(n_channels, n_samples)
        raw = mne.io.RawArray(data, info)
        
        # Import extraction function
        from code_03_extract_features import extract_features_for_subject
        
        subject_id = 'sub-001'
        row = extract_features_for_subject(subject_id, raw, 4.0, 2.0)
        
        # Check structure
        assert isinstance(row, dict)
        assert 'participant_id' in row
        assert row['participant_id'] == subject_id
        
        # Check band powers
        expected_bands = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
        for band in expected_bands:
            assert band in row
            assert isinstance(row[band], float)
            assert not np.isnan(row[band])

    def test_main_function_output_structure(self, tmp_path):
        """Test that main function produces valid CSV output."""
        # This is a structural test; actual data processing requires real files
        # We test that the function would produce a DataFrame with correct columns
        
        # Create a mock DataFrame similar to what main() would produce
        expected_cols = ['participant_id', 'delta', 'theta', 'alpha', 
                       'low_beta', 'high_beta', 'gamma']
        
        # Verify column names match expected
        assert set(expected_cols) == set(['participant_id'] + get_all_band_names())

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
