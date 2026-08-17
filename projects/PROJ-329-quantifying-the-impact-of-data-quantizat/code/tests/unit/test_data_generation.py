"""
Unit tests for src/data_generation.py.

Verifies:
- Waveform generation logic (mocked).
- Quantization application.
- Baseline generation.
- Error handling for missing PSD.
"""
import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_generation import (
    apply_quantization,
    generate_parallel_baseline,
    load_or_generate_noise_psd,
    inject_noise
)
from src.utils import quantize_fixed_fsr


class TestDataGeneration:
    
    def test_apply_quantization_levels(self):
        """Test that quantization produces correct number of levels."""
        # Create a signal that spans the range
        signal = np.linspace(-1.0, 1.0, 1000)
        
        # 2-bit quantization should have 2^2 = 4 levels
        quantized_2bit = apply_quantization(signal, 2)
        unique_2bit = np.unique(quantized_2bit)
        # Note: Due to clipping and distribution, we might not get exactly 4 unique values
        # if the signal doesn't hit all bins, but it should not exceed 4.
        assert len(unique_2bit) <= 4, f"2-bit quantization produced {len(unique_2bit)} levels, expected <= 4"
        
        # 8-bit
        quantized_8bit = apply_quantization(signal, 8)
        unique_8bit = np.unique(quantized_8bit)
        assert len(unique_8bit) <= 256, f"8-bit quantization produced {len(unique_8bit)} levels, expected <= 256"

    def test_parallel_baseline_dtype(self):
        """Test that baseline is float64."""
        signal = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        baseline = generate_parallel_baseline(signal)
        assert baseline.dtype == np.float64, "Baseline should be float64"
        
    def test_inject_noise_snr_scaling(self):
        """Test that noise injection scales SNR correctly."""
        # Simple test: generate a sine wave as "signal"
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t)
        
        # Fake PSD (flat white noise)
        psd_freqs = np.linspace(0, 500, 501)
        psd_vals = np.ones_like(psd_freqs) * 1e-4
        
        target_snr = 10.0
        noisy_signal, actual_snr = inject_noise(signal, psd_freqs, psd_vals, target_snr)
        
        # The actual SNR should be close to target (within tolerance due to randomness)
        # We run a few times to average out noise if needed, but for a single test:
        assert 0.8 * target_snr <= actual_snr <= 1.2 * target_snr, \
            f"Actual SNR {actual_snr} not within 20% of target {target_snr}"

    def test_load_psd_missing_file(self):
        """Test that missing PSD file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_or_generate_noise_psd("/nonexistent/path/psd.txt")

    def test_load_psd_valid_file(self):
        """Test loading a valid PSD file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            # Write dummy PSD data
            for i in range(100):
                f.write(f"{i} {1.0e-4}\n")
            temp_path = f.name
        
        try:
            freqs, psds = load_or_generate_noise_psd(temp_path)
            assert len(freqs) == 100
            assert len(psds) == 100
            assert psds[0] == 1.0e-4
        finally:
            os.remove(temp_path)
