"""
Unit tests for compression modules.
Tests lossless compression bitwise equality and lossy compression metrics.
"""
import os
import sys
import tempfile
import gzip
import bz2
import lzma
import struct
import math
from pathlib import Path
from typing import Tuple, List

import pytest
import numpy as np

# Add code directory to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Import compression modules (these will be implemented in T019/T020)
# We use a try/except to allow the test file to be written before implementation
# In a real CI run, these modules must exist.
try:
    from src.compression.lossless import compress, decompress
    LOSSLESS_AVAILABLE = True
except ImportError:
    LOSSLESS_AVAILABLE = False
    # Mock functions for testing file existence if modules are missing
    def compress(data: bytes, method: str = "gzip", level: int = 9) -> bytes:
        if method == "gzip":
            return gzip.compress(data)
        elif method == "bz2":
            return bz2.compress(data)
        elif method == "lzma":
            return lzma.compress(data)
        raise ValueError(f"Unknown method: {method}")

    def decompress(data: bytes, method: str = "gzip") -> bytes:
        if method == "gzip":
            return gzip.decompress(data)
        elif method == "bz2":
            return bz2.decompress(data)
        elif method == "lzma":
            return lzma.decompress(data)
        raise ValueError(f"Unknown method: {method}")

try:
    from src.compression.metrics import calculate_mse, calculate_snr_degradation
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    def calculate_mse(original: np.ndarray, reconstructed: np.ndarray) -> float:
        return float(np.mean((original - reconstructed) ** 2))

    def calculate_snr_degradation(original: np.ndarray, reconstructed: np.ndarray) -> float:
        # Simplified SNR calculation
        signal_power = np.mean(original ** 2)
        noise_power = np.mean((original - reconstructed) ** 2)
        if noise_power == 0:
            return float('inf')
        return 10 * math.log10(signal_power / noise_power)


@pytest.fixture
def sample_waveform_data():
    """Generate a realistic GW strain time series for testing."""
    np.random.seed(42)
    # Simulate a noisy strain signal with a sine component (approximating a GW signal)
    t = np.linspace(0, 1, 4096)  # 4096 points, 1 second duration
    frequency = 100  # 100 Hz signal
    signal = 1e-21 * np.sin(2 * np.pi * frequency * t)
    noise = 1e-23 * np.random.randn(len(t))
    strain = signal + noise
    return strain.astype(np.float64)


@pytest.fixture
def sample_waveform_bytes(sample_waveform_data):
    """Convert waveform to bytes for compression testing."""
    return sample_waveform_data.tobytes()


class TestLosslessCompression:
    """Tests for lossless compression methods (gzip, bz2, lzma)."""

    @pytest.mark.parametrize("method,level", [
        ("gzip", 1), ("gzip", 5), ("gzip", 9),
        ("bz2", 1), ("bz2", 5), ("bz2", 9),
        ("lzma", 0), ("lzma", 5), ("lzma", 9),
    ])
    def test_lossless_bitwise_equality(self, sample_waveform_bytes, method, level):
        """
        Assert that lossless compression/decompression results in exact bitwise equality.
        MSE between original and reconstructed must be exactly 0.
        """
        if not LOSSLESS_AVAILABLE:
            pytest.skip("Lossless compression modules not yet implemented")

        # Compress
        compressed = compress(sample_waveform_bytes, method=method, level=level)
        assert len(compressed) < len(sample_waveform_bytes), \
            f"Compression {method} level {level} did not reduce size"

        # Decompress
        decompressed = decompress(compressed, method=method)

        # Assert bitwise equality
        assert decompressed == sample_waveform_bytes, \
            f"Lossless {method} level {level} failed bitwise equality check"

        # Assert MSE is exactly 0
        original_array = np.frombuffer(sample_waveform_bytes, dtype=np.float64)
        reconstructed_array = np.frombuffer(decompressed, dtype=np.float64)
        
        mse = calculate_mse(original_array, reconstructed_array)
        assert mse == 0.0, \
            f"Lossless {method} level {level} resulted in non-zero MSE: {mse}"

    def test_lossless_handles_empty_data(self):
        """Test that lossless compression handles empty input correctly."""
        if not LOSSLESS_AVAILABLE:
            pytest.skip("Lossless compression modules not yet implemented")
        
        empty_bytes = b""
        compressed = compress(empty_bytes, method="gzip")
        decompressed = decompress(compressed, method="gzip")
        assert decompressed == empty_bytes

    def test_lossless_handles_single_byte(self):
        """Test that lossless compression handles single byte correctly."""
        if not LOSSLESS_AVAILABLE:
            pytest.skip("Lossless compression modules not yet implemented")
        
        single_byte = b"\x00"
        compressed = compress(single_byte, method="gzip")
        decompressed = decompress(compressed, method="gzip")
        assert decompressed == single_byte


class TestLossyCompressionMetrics:
    """Tests for lossy compression metrics (MSE, SNR degradation)."""

    def test_mse_zero_for_identical_arrays(self, sample_waveform_data):
        """Assert MSE is 0 when comparing identical arrays."""
        mse = calculate_mse(sample_waveform_data, sample_waveform_data)
        assert mse == 0.0

    def test_mse_positive_for_different_arrays(self, sample_waveform_data):
        """Assert MSE is positive when arrays differ."""
        modified = sample_waveform_data * 1.1  # Scale by 10%
        mse = calculate_mse(sample_waveform_data, modified)
        assert mse > 0.0

    def test_snr_degradation_positive_for_noisy_reconstruction(self, sample_waveform_data):
        """
        Assert SNR degradation is positive (in dB) when reconstruction has noise.
        This simulates a lossy compression scenario.
        """
        if not METRICS_AVAILABLE:
            pytest.skip("Metrics modules not yet implemented")

        # Simulate a noisy reconstruction
        noise = 1e-24 * np.random.randn(len(sample_waveform_data))
        noisy_reconstruction = sample_waveform_data + noise

        snr_deg = calculate_snr_degradation(sample_waveform_data, noisy_reconstruction)
        
        # SNR degradation should be a finite positive number (in dB)
        assert isinstance(snr_deg, float), "SNR degradation must be a float"
        assert snr_deg > 0.0, \
            f"SNR degradation should be positive for noisy reconstruction, got {snr_deg}"

    def test_snr_degradation_infinite_for_perfect_reconstruction(self, sample_waveform_data):
        """Assert SNR degradation is infinite (or very large) for perfect reconstruction."""
        if not METRICS_AVAILABLE:
            pytest.skip("Metrics modules not yet implemented")

        snr_deg = calculate_snr_degradation(sample_waveform_data, sample_waveform_data)
        
        # With zero noise, SNR should be infinite
        assert snr_deg == float('inf') or snr_deg > 1000.0, \
            f"SNR degradation should be very high for perfect reconstruction, got {snr_deg}"

    def test_mse_precision(self, sample_waveform_data):
        """Test MSE calculation precision with small differences."""
        small_diff = sample_waveform_data + 1e-30
        mse = calculate_mse(sample_waveform_data, small_diff)
        # Should be a very small positive number
        assert 0 < mse < 1e-29, f"MSE precision issue: {mse}"


class TestCompressionIntegration:
    """Integration tests combining compression and metrics."""

    @pytest.mark.parametrize("method", ["gzip", "bz2", "lzma"])
    def test_lossless_roundtrip_preserves_snr(self, sample_waveform_data, method):
        """Assert that lossless compression preserves SNR (degradation is 0)."""
        if not LOSSLESS_AVAILABLE or not METRICS_AVAILABLE:
            pytest.skip("Required modules not yet implemented")

        original_bytes = sample_waveform_data.tobytes()
        compressed = compress(original_bytes, method=method)
        decompressed_bytes = decompress(compressed, method=method)
        
        reconstructed = np.frombuffer(decompressed_bytes, dtype=np.float64)
        
        snr_deg = calculate_snr_degradation(sample_waveform_data, reconstructed)
        assert snr_deg == 0.0 or snr_deg == float('inf'), \
            f"Lossless {method} should result in 0 SNR degradation"

    def test_quantization_simulation(self, sample_waveform_data):
        """Simulate a simple quantization lossy compression and verify metrics."""
        if not METRICS_AVAILABLE:
            pytest.skip("Metrics modules not yet implemented")

        # Simulate 4-bit quantization (very lossy)
        original_floats = sample_waveform_data
        min_val = np.min(original_floats)
        max_val = np.max(original_floats)
        range_val = max_val - min_val
        
        # Quantize to 16 levels (4 bits)
        quantized_indices = np.floor((original_floats - min_val) / range_val * 15).astype(int)
        quantized_indices = np.clip(quantized_indices, 0, 15)
        reconstructed_floats = min_val + (quantized_indices / 15.0) * range_val

        mse = calculate_mse(original_floats, reconstructed_floats)
        snr_deg = calculate_snr_degradation(original_floats, reconstructed_floats)

        # Verify metrics are reasonable for quantization
        assert mse > 0, "Quantization should introduce error"
        assert snr_deg > 0, "Quantization should degrade SNR"
        # SNR degradation for 4-bit quantization is typically significant (> 10 dB)
        assert snr_deg > 5.0, \
            f"4-bit quantization SNR degradation should be > 5 dB, got {snr_deg}"