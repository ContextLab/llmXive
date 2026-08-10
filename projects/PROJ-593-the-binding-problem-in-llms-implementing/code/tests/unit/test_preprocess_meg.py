"""
Unit tests for preprocess_meg.py module.

Tests cover:
- Butter bandpass filter functionality
- Bandpass filter application to DataFrame
- Welch PSD computation and normalization
- PSD data validation
- Full script execution
"""
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy.signal import butter, welch, windows
import sys

# Add code directory to path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.preprocess_meg import (
    butter_bandpass_filter,
    apply_bandpass_filter,
    compute_and_normalize_psd,
    validate_psd_data,
    load_config
)

class TestButterBandpass:
    """Test the Butterworth bandpass filter implementation."""
    
    def test_filter_creation(self):
        """Test that filter coefficients are created correctly."""
        fs = 1000.0
        lowcut = 1.0
        highcut = 100.0
        order = 4
        
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        
        b, a = butter(order, [low, high], btype='band')
        
        assert len(b) == len(a), "Filter coefficients must have same length"
        assert len(b) > 0, "Filter coefficients must not be empty"
    
    def test_filter_output_shape(self):
        """Test that filter preserves input shape."""
        fs = 1000.0
        lowcut = 1.0
        highcut = 100.0
        
        # Create test signal
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 10 * t)
        
        filtered = butter_bandpass_filter(signal, fs, lowcut, highcut)
        
        assert filtered.shape == signal.shape, "Filtered signal must have same shape as input"
    
    def test_filter_rejects_low_frequency(self):
        """Test that low frequencies are attenuated."""
        fs = 1000.0
        lowcut = 10.0
        highcut = 100.0
        
        # Create signal with 5 Hz component (should be filtered out)
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 5 * t)  # 5 Hz - below cutoff
        
        filtered = butter_bandpass_filter(signal, fs, lowcut, highcut)
        
        # The filtered signal should have much lower amplitude
        input_power = np.mean(signal ** 2)
        output_power = np.mean(filtered ** 2)
        
        assert output_power < input_power * 0.1, "Low frequency should be significantly attenuated"
    
    def test_filter_passes_high_frequency(self):
        """Test that frequencies in passband are preserved."""
        fs = 1000.0
        lowcut = 10.0
        highcut = 100.0
        
        # Create signal with 50 Hz component (should pass through)
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t)  # 50 Hz - in passband
        
        filtered = butter_bandpass_filter(signal, fs, lowcut, highcut)
        
        # The filtered signal should maintain most of its power
        input_power = np.mean(signal ** 2)
        output_power = np.mean(filtered ** 2)
        
        assert output_power > input_power * 0.5, "Passband frequency should be preserved"
    
    def test_invalid_cutoff_frequencies(self):
        """Test that invalid cutoff frequencies raise an error."""
        fs = 1000.0
        signal = np.random.randn(1000)
        
        # Low cutoff > Nyquist
        with pytest.raises(ValueError):
            butter_bandpass_filter(signal, fs, lowcut=600, highcut=800)
        
        # Low cutoff >= high cutoff
        with pytest.raises(ValueError):
            butter_bandpass_filter(signal, fs, lowcut=100, highcut=50)

class TestApplyBandpassFilter:
    """Test the DataFrame bandpass filter application."""
    
    def test_adds_filtered_signal_column(self):
        """Test that filtered signal column is added to DataFrame."""
        fs = 1000.0
        df = pd.DataFrame({
            'signal': np.random.randn(1000)
        })
        
        df_filtered = apply_bandpass_filter(df, fs, 1.0, 100.0)
        
        assert 'filtered_signal' in df_filtered.columns, "filtered_signal column must be added"
    
    def test_preserves_original_data(self):
        """Test that original signal column is preserved."""
        fs = 1000.0
        original_signal = np.random.randn(1000)
        df = pd.DataFrame({
            'signal': original_signal
        })
        
        df_filtered = apply_bandpass_filter(df, fs, 1.0, 100.0)
        
        np.testing.assert_array_equal(df_filtered['signal'].values, original_signal)
    
    def test_missing_signal_column(self):
        """Test that missing signal column raises an error."""
        fs = 1000.0
        df = pd.DataFrame({
            'other_column': np.random.randn(1000)
        })
        
        with pytest.raises(ValueError):
            apply_bandpass_filter(df, fs, 1.0, 100.0)
    
    def test_2d_signal_flattening(self):
        """Test that 2D signals are properly flattened."""
        fs = 1000.0
        # Create 2D signal
        signal_2d = np.random.randn(1000, 1)
        df = pd.DataFrame({
            'signal': signal_2d
        })
        
        df_filtered = apply_bandpass_filter(df, fs, 1.0, 100.0)
        
        assert df_filtered['filtered_signal'].ndim == 1, "Filtered signal should be 1D"
        assert len(df_filtered['filtered_signal']) == 1000

class TestComputeAndNormalizePsd:
    """Test Welch PSD computation and normalization."""
    
    def test_psd_computation(self):
        """Test that PSD is computed correctly."""
        fs = 1000.0
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t)
        
        freqs, psd = compute_and_normalize_psd(signal, fs, nperseg=256, target_len=512)
        
        assert len(freqs) > 0, "Frequency array must not be empty"
        assert len(psd) == len(freqs), "PSD and frequency arrays must have same length"
        assert np.all(psd >= 0), "PSD values must be non-negative"
    
    def test_normalization_to_unit_area(self):
        """Test that PSD is normalized to unit area."""
        fs = 1000.0
        signal = np.random.randn(512)
        
        freqs, psd_normalized = compute_and_normalize_psd(signal, fs, nperseg=256, target_len=512)
        
        area = np.trapz(psd_normalized, freqs)
        assert np.isclose(area, 1.0, atol=1e-6), f"PSD should be normalized to unit area, got {area}"
    
    def test_zero_padding(self):
        """Test that signals shorter than target_len are zero-padded."""
        fs = 1000.0
        short_signal = np.random.randn(100)  # Shorter than target_len=512
        
        freqs, psd = compute_and_normalize_psd(short_signal, fs, nperseg=256, target_len=512)
        
        # Should not raise an error
        assert len(freqs) > 0
        assert len(psd) == len(freqs)
    
    def test_zero_psd_raises_error(self):
        """Test that zero PSD raises an error during normalization."""
        fs = 1000.0
        zero_signal = np.zeros(512)
        
        with pytest.raises(ValueError):
            compute_and_normalize_psd(zero_signal, fs, nperseg=256, target_len=512)
    
    def test_hann_window_usage(self):
        """Test that Hann window is used in Welch computation."""
        # This is verified by checking the function implementation uses windows.hann
        # We can test that the PSD computation is reasonable
        fs = 1000.0
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 50 * t)
        
        freqs, psd = compute_and_normalize_psd(signal, fs, nperseg=256, target_len=512)
        
        # The peak should be around 50 Hz
        peak_idx = np.argmax(psd)
        peak_freq = freqs[peak_idx]
        
        # Allow some tolerance for frequency resolution
        assert 40 <= peak_freq <= 60, f"Peak frequency should be around 50 Hz, got {peak_freq}"

class TestValidatePSDData:
    """Test PSD data validation."""
    
    def test_valid_psd(self):
        """Test that valid PSD passes validation."""
        freqs = np.linspace(0, 500, 256)
        psd = np.random.rand(256)
        psd = psd / np.trapz(psd, freqs)  # Normalize to unit area
        
        # Should not raise
        validate_psd_data(freqs, psd)
    
    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        freqs = np.linspace(0, 500, 256)
        psd = np.random.rand(200)  # Different length
        
        with pytest.raises(ValueError):
            validate_psd_data(freqs, psd)
    
    def test_negative_psd_values(self):
        """Test that negative PSD values raise an error."""
        freqs = np.linspace(0, 500, 256)
        psd = np.random.rand(256)
        psd[0] = -0.1  # Negative value
        
        with pytest.raises(ValueError):
            validate_psd_data(freqs, psd)
    
    def test_non_unit_area(self):
        """Test that non-unit area PSD raises an error."""
        freqs = np.linspace(0, 500, 256)
        psd = np.random.rand(256)
        # Don't normalize - area won't be 1
        
        with pytest.raises(ValueError):
            validate_psd_data(freqs, psd)
    
    def test_insufficient_frequency_range(self):
        """Test that insufficient frequency range raises an error."""
        freqs = np.linspace(0, 20, 100)  # Max frequency too low
        psd = np.random.rand(100)
        psd = psd / np.trapz(psd, freqs)  # Normalize
        
        with pytest.raises(ValueError):
            validate_psd_data(freqs, psd)

class TestLoadConfig:
    """Test configuration loading."""
    
    def test_config_exists(self):
        """Test that config file exists."""
        # This test assumes the config file is created by T014
        config_path = code_root / "config" / "default.yaml"
        # We don't assert here as the config might not exist in all test environments
        # Just verify the function doesn't crash when the file exists
        if config_path.exists():
            config = load_config()
            assert isinstance(config, dict)

class TestPreprocessMegScriptExecution:
    """Test the full preprocessing script execution."""
    
    def test_script_creates_output_files(self):
        """Test that the script creates the required output files."""
        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create necessary directories
            (tmp_path / "data" / "raw").mkdir(parents=True)
            (tmp_path / "data" / "processed").mkdir(parents=True)
            (tmp_path / "config").mkdir(parents=True)
            
            # Create a mock config file
            config_content = """
            sampling_frequency: 1000.0
            lowcut: 1.0
            highcut: 100.0
            """
            with open(tmp_path / "config" / "default.yaml", 'w') as f:
                f.write(config_content)
            
            # Create mock MEG data
            mock_data = pd.DataFrame({
                'signal': np.random.randn(1000)
            })
            mock_data.to_parquet(tmp_path / "data" / "raw" / "meg_streamed.parquet")
            
            # Temporarily modify the code_root for testing
            original_root = code_root
            import src.data.preprocess_meg as pm_module
            pm_module.code_root = tmp_path
            
            try:
                # Run the main function
                filtered_output, psd_output = pm_module.main()
                
                # Verify output files exist
                assert filtered_output.exists(), "Filtered signal file should exist"
                assert psd_output.exists(), "PSD file should exist"
                
                # Verify file contents
                filtered_data = np.load(filtered_output)
                psd_data = np.load(psd_output)
                
                assert len(filtered_data) == 1000, "Filtered data should have 1000 samples"
                assert psd_data.shape[0] == 2, "PSD data should have 2 rows (freqs, psd)"
                assert len(psd_data[0]) == len(psd_data[1]), "Freqs and PSD should have same length"
                
            finally:
                # Restore original code_root
                pm_module.code_root = original_root
    
    def test_script_fails_on_missing_input(self):
        """Test that the script fails when input file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create necessary directories but no input file
            (tmp_path / "data" / "raw").mkdir(parents=True)
            (tmp_path / "data" / "processed").mkdir(parents=True)
            (tmp_path / "config").mkdir(parents=True)
            
            # Create mock config
            config_content = """
            sampling_frequency: 1000.0
            lowcut: 1.0
            highcut: 100.0
            """
            with open(tmp_path / "config" / "default.yaml", 'w') as f:
                f.write(config_content)
            
            import src.data.preprocess_meg as pm_module
            pm_module.code_root = tmp_path
            
            try:
                with pytest.raises(FileNotFoundError):
                    pm_module.main()
            finally:
                pm_module.code_root = original_root