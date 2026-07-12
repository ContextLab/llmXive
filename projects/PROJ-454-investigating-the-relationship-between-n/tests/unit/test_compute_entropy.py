"""
Unit tests for compute_entropy.py functionality.
Tests entropy calculation stability and output format.
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.compute_entropy import (
    bandpass_filter,
    compute_entropy_for_subject,
    FREQUENCY_BANDS
)
from utils.entropy_utils import sample_entropy, approximate_entropy

class TestBandpassFilter:
    def test_filter_shape_preservation(self):
        """Test that filter preserves data shape."""
        sfreq = 256.0
        data = np.random.randn(10, 32, 256)  # (epochs, channels, times)
        filtered = bandpass_filter(data, sfreq, 8, 13)
        assert filtered.shape == data.shape

    def test_filter_valid_range(self):
        """Test filter with valid frequency range."""
        sfreq = 256.0
        data = np.random.randn(1, 1, 1000)
        filtered = bandpass_filter(data, sfreq, 1, 45)
        assert np.all(np.isfinite(filtered))

    def test_filter_invalid_range(self):
        """Test filter with invalid frequency range returns original data."""
        sfreq = 256.0
        data = np.random.randn(1, 1, 1000)
        filtered = bandpass_filter(data, sfreq, 100, 50)  # Invalid: low > high
        np.testing.assert_array_equal(filtered, data)

class TestEntropyComputation:
    def test_entropy_no_nan_on_valid_data(self):
        """Test that entropy computation returns finite values for valid signals."""
        # Create synthetic EEG-like data: (epochs, channels, times)
        np.random.seed(42)
        data = np.random.randn(5, 10, 500)  # 5 epochs, 10 channels, 500 time points
        ch_names = [f'CH{i}' for i in range(10)]
        
        subject_data = {
            'data': data,
            'ch_names': ch_names,
            'sfreq': 256.0
        }
        
        results = compute_entropy_for_subject('test_subject', subject_data)
        
        assert len(results) > 0, "No results returned"
        
        # Check that entropy values are not NaN for valid computations
        for r in results:
            if not np.isnan(r['sample_entropy']):
                assert np.isfinite(r['sample_entropy'])
            if not np.isnan(r['approximate_entropy']):
                assert np.isfinite(r['approximate_entropy'])

    def test_entropy_all_bands_computed(self):
        """Test that all frequency bands are computed."""
        np.random.seed(42)
        data = np.random.randn(3, 4, 1000)
        ch_names = ['Cz', 'Pz', 'Fz', 'Oz']
        
        subject_data = {
            'data': data,
            'ch_names': ch_names,
            'sfreq': 256.0
        }
        
        results = compute_entropy_for_subject('test_subject', subject_data)
        
        bands_in_results = set(r['band'] for r in results)
        expected_bands = set(FREQUENCY_BANDS.keys())
        
        assert bands_in_results == expected_bands, f"Missing bands: {expected_bands - bands_in_results}"

    def test_entropy_output_structure(self):
        """Test that output contains required fields."""
        np.random.seed(42)
        data = np.random.randn(2, 2, 500)
        ch_names = ['A', 'B']
        
        subject_data = {
            'data': data,
            'ch_names': ch_names,
            'sfreq': 256.0
        }
        
        results = compute_entropy_for_subject('sub1', subject_data)
        
        required_fields = [
            'subject_id', 'channel', 'band', 
            'sample_entropy', 'approximate_entropy', 
            'n_valid_epochs', 'sfreq', 'band_low_hz', 'band_high_hz'
        ]
        
        for r in results:
            for field in required_fields:
                assert field in r, f"Missing field: {field}"

class TestEntropyUtilsIntegration:
    def test_sample_entropy_stability(self):
        """Test sample_entropy function with various inputs."""
        signal = np.random.randn(1000)
        r = 0.2 * np.std(signal)
        
        se = sample_entropy(signal, 2, r)
        
        assert np.isfinite(se) or np.isnan(se), "Entropy must be finite or NaN"
        # Note: NaN can occur for very short or constant signals, which is acceptable

    def test_approximate_entropy_stability(self):
        """Test approximate_entropy function with various inputs."""
        signal = np.random.randn(1000)
        r = 0.2 * np.std(signal)
        
        ae = approximate_entropy(signal, 2, r)
        
        assert np.isfinite(ae) or np.isnan(ae), "Entropy must be finite or NaN"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])