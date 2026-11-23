import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
import sys

# Add parent to path if running standalone, though pytest should handle it
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.analysis.snr_verification import (
    calculate_target_band_snr,
    verify_oscillatory_snr,
    load_activation_time_series,
    load_control_run_comparison
)
from src.analysis.spectral import compute_welch_psd

class TestSNRVerification:
    
    def test_calculate_target_band_snr_with_known_signal(self):
        """
        Test SNR calculation with a synthetic signal containing a strong 40Hz component.
        """
        fs = 1000.0
        duration = 1.0
        t = np.arange(0, duration, 1/fs)
        # 40Hz sine wave
        signal = np.sin(2 * np.pi * 40 * t)
        # Add some noise
        noise = np.random.normal(0, 0.1, len(t))
        noisy_signal = signal + noise
        
        freqs, psd = compute_welch_psd(noisy_signal, fs=fs, nperseg=256)
        
        target_p, adj_p, snr_db = calculate_target_band_snr(psd, freqs)
        
        # The SNR should be positive and reasonably high for this synthetic signal
        assert snr_db > 0, "SNR should be positive for a strong signal"
        assert target_p > adj_p, "Target band power should be higher than adjacent"

    def test_calculate_target_band_snr_low_snr(self):
        """
        Test SNR calculation with a signal where noise dominates.
        """
        fs = 1000.0
        duration = 1.0
        t = np.arange(0, duration, 1/fs)
        # No 40Hz component, just noise
        signal = np.random.normal(0, 1.0, len(t))
        
        freqs, psd = compute_welch_psd(signal, fs=fs, nperseg=256)
        
        target_p, adj_p, snr_db = calculate_target_band_snr(psd, freqs)
        
        # SNR might be negative or close to 0
        assert isinstance(snr_db, float)

    def test_load_activation_time_series(self):
        """
        Test loading of activation time series from numpy file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_activations.npy"
            data = np.random.rand(10, 100)
            np.save(path, data)
            
            loaded = load_activation_time_series(str(path))
            assert loaded.shape == data.shape
            np.testing.assert_array_equal(loaded, data)

    def test_load_control_run_comparison(self):
        """
        Test loading of control run comparison JSON.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_control.json"
            data = {
                "oscillatory_coherence": 0.8,
                "baseline_coherence": 0.4,
                "coherence_difference": 0.4
            }
            with open(path, 'w') as f:
                json.dump(data, f)
            
            loaded = load_control_run_comparison(str(path))
            assert loaded["oscillatory_coherence"] == 0.8
            assert loaded["baseline_coherence"] == 0.4

    def test_verify_oscillatory_snr_integration(self):
        """
        Integration test for the full verification function.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create synthetic activation data with a 40Hz component
            fs = 1000.0
            duration = 1.0
            t = np.arange(0, duration, 1/fs)
            signal = np.sin(2 * np.pi * 40 * t) + np.random.normal(0, 0.1, len(t))
            activations = np.array([signal])
            
            act_path = tmpdir / "activation_oscillatory.npy"
            np.save(act_path, activations)
            
            # Create control run data
            control_path = tmpdir / "control_run_comparison.json"
            control_data = {
                "oscillatory_coherence": 0.9,
                "baseline_coherence": 0.3,
                "coherence_difference": 0.6
            }
            with open(control_path, 'w') as f:
                json.dump(control_data, f)
            
            # Run verification
            result = verify_oscillatory_snr(
                str(act_path), 
                str(control_path), 
                fs=fs, 
                nperseg=256
            )
            
            assert "status" in result
            assert "snr_db" in result
            assert "target_band_power" in result
            assert "adjacent_band_power" in result
            
            # For our synthetic signal, SNR should be > 0
            assert result["snr_db"] > 0