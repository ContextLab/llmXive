"""
Unit tests for lossless compression bitwise equality.

This module verifies that lossless compression algorithms (gzip, bzip2, lzma)
preserve data integrity exactly. When decompressed, the data must be bitwise
identical to the original, resulting in MSE == 0.

Tests:
  - test_lossless_gzip_bitwise_equality: Verifies gzip compression/decompression
  - test_lossless_bzip2_bitwise_equality: Verifies bzip2 compression/decompression
  - test_lossless_lzma_bitwise_equality: Verifies lzma compression/decompression
  - test_lossless_compression_preserves_float_precision: Ensures float64 data
    maintains exact bit representation after round-trip
"""

import os
import sys
import tempfile
import json
import numpy as np
import pytest
from pathlib import Path
import gzip
import bz2
import lzma

# Add code directory to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.config import get_project_root, ensure_dir


class TestLosslessCompression:
    """Test suite for lossless compression bitwise equality."""

    @pytest.fixture
    def sample_waveform_data(self):
        """Generate realistic gravitational wave strain data for testing."""
        # Create a synthetic CBC signal with noise (simulating real GW data)
        duration = 4.0  # seconds
        sample_rate = 4096  # Hz
        n_samples = duration * sample_rate
        
        # Generate time array
        t = np.linspace(0, duration, n_samples)
        
        # Create a simple chirp signal (inspiral phase)
        # f(t) = f0 * (1 - t/tau)^(-3/8)
        f0 = 30.0  # Hz
        tau = 2.0  # seconds
        frequency = f0 * (1 - t/tau)**(-3/8)
        frequency = np.clip(frequency, f0, 500.0)  # Cap at 500 Hz
        
        # Amplitude evolution
        amplitude = (1 - t/tau)**(-1/4)
        amplitude = np.clip(amplitude, 0, 10.0)
        
        # Phase evolution
        phase = 2 * np.pi * np.cumsum(frequency) / sample_rate
        
        # Generate strain signal
        strain = amplitude * np.cos(phase)
        
        # Add realistic Gaussian noise (SNR ~ 10)
        noise_std = np.std(strain) / 10.0
        noise = np.random.normal(0, noise_std, n_samples)
        
        # Combine signal and noise
        waveform_data = strain + noise
        
        # Ensure we have float64 precision (as used in real GW data)
        waveform_data = waveform_data.astype(np.float64)
        
        return waveform_data

    @pytest.fixture
    def temp_compression_dir(self):
        """Create a temporary directory for compression test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def _save_waveform_to_json(self, data, filepath):
        """Save waveform data to a JSON file (simulating real data storage)."""
        metadata = {
            "event_id": "test_event_001",
            "detector": "LIGO_Hanford",
            "sample_rate": 4096,
            "duration": 4.0,
            "n_samples": len(data),
            "true_parameters": {
                "mass_1": 30.0,
                "mass_2": 25.0,
                "spin_1": 0.5,
                "spin_2": 0.3
            }
        }
        
        output = {
            "metadata": metadata,
            "strain_data": data.tolist()
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f)

    def _load_waveform_from_json(self, filepath):
        """Load waveform data from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return np.array(data["strain_data"], dtype=np.float64), data["metadata"]

    def _compute_mse(self, original, reconstructed):
        """Compute Mean Squared Error between original and reconstructed data."""
        original = np.array(original)
        reconstructed = np.array(reconstructed)
        
        assert original.shape == reconstructed.shape, \
            f"Shape mismatch: {original.shape} vs {reconstructed.shape}"
        
        mse = np.mean((original - reconstructed) ** 2)
        return mse

    def test_lossless_gzip_bitwise_equality(self, sample_waveform_data, temp_compression_dir):
        """
        Test that gzip compression produces bitwise identical data after decompression.
        
        Assert: MSE == 0 (bitwise equality)
        """
        # Save original data
        original_file = temp_compression_dir / "original.json"
        self._save_waveform_to_json(sample_waveform_data, original_file)
        
        # Read original file as bytes
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        # Compress with gzip
        compressed_file = temp_compression_dir / "compressed.gz"
        with gzip.open(compressed_file, 'wb') as f:
            f.write(original_bytes)
        
        # Decompress
        decompressed_bytes = gzip.open(compressed_file, 'rb').read()
        
        # Verify bitwise equality
        assert original_bytes == decompressed_bytes, \
            "Gzip compression/decompression failed bitwise equality check"
        
        # Load and verify data integrity
        decompressed_file = temp_compression_dir / "decompressed.json"
        with open(decompressed_file, 'wb') as f:
            f.write(decompressed_bytes)
        
        reconstructed_data, _ = self._load_waveform_from_json(decompressed_file)
        
        # Compute MSE
        mse = self._compute_mse(sample_waveform_data, reconstructed_data)
        
        # ASSERTION: MSE must be exactly 0 for lossless compression
        assert mse == 0, f"Lossless gzip compression failed: MSE = {mse} (expected 0)"

    def test_lossless_bzip2_bitwise_equality(self, sample_waveform_data, temp_compression_dir):
        """
        Test that bzip2 compression produces bitwise identical data after decompression.
        
        Assert: MSE == 0 (bitwise equality)
        """
        # Save original data
        original_file = temp_compression_dir / "original.json"
        self._save_waveform_to_json(sample_waveform_data, original_file)
        
        # Read original file as bytes
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        # Compress with bzip2
        compressed_file = temp_compression_dir / "compressed.bz2"
        with bz2.open(compressed_file, 'wb') as f:
            f.write(original_bytes)
        
        # Decompress
        decompressed_bytes = bz2.open(compressed_file, 'rb').read()
        
        # Verify bitwise equality
        assert original_bytes == decompressed_bytes, \
            "Bzip2 compression/decompression failed bitwise equality check"
        
        # Load and verify data integrity
        decompressed_file = temp_compression_dir / "decompressed.json"
        with open(decompressed_file, 'wb') as f:
            f.write(decompressed_bytes)
        
        reconstructed_data, _ = self._load_waveform_from_json(decompressed_file)
        
        # Compute MSE
        mse = self._compute_mse(sample_waveform_data, reconstructed_data)
        
        # ASSERTION: MSE must be exactly 0 for lossless compression
        assert mse == 0, f"Lossless bzip2 compression failed: MSE = {mse} (expected 0)"

    def test_lossless_lzma_bitwise_equality(self, sample_waveform_data, temp_compression_dir):
        """
        Test that lzma compression produces bitwise identical data after decompression.
        
        Assert: MSE == 0 (bitwise equality)
        """
        # Save original data
        original_file = temp_compression_dir / "original.json"
        self._save_waveform_to_json(sample_waveform_data, original_file)
        
        # Read original file as bytes
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        # Compress with lzma
        compressed_file = temp_compression_dir / "compressed.xz"
        with lzma.open(compressed_file, 'wb') as f:
            f.write(original_bytes)
        
        # Decompress
        decompressed_bytes = lzma.open(compressed_file, 'rb').read()
        
        # Verify bitwise equality
        assert original_bytes == decompressed_bytes, \
            "LZMA compression/decompression failed bitwise equality check"
        
        # Load and verify data integrity
        decompressed_file = temp_compression_dir / "decompressed.json"
        with open(decompressed_file, 'wb') as f:
            f.write(decompressed_bytes)
        
        reconstructed_data, _ = self._load_waveform_from_json(decompressed_file)
        
        # Compute MSE
        mse = self._compute_mse(sample_waveform_data, reconstructed_data)
        
        # ASSERTION: MSE must be exactly 0 for lossless compression
        assert mse == 0, f"Lossless lzma compression failed: MSE = {mse} (expected 0)"

    def test_lossless_compression_preserves_float_precision(self, sample_waveform_data, temp_compression_dir):
        """
        Test that lossless compression preserves exact float64 bit representation.
        
        This is critical for gravitational wave data where small numerical differences
        can affect parameter estimation results.
        
        Assert: MSE == 0 (exact bit preservation)
        """
        # Save original data
        original_file = temp_compression_dir / "original.json"
        self._save_waveform_to_json(sample_waveform_data, original_file)
        
        # Read original file as bytes
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        # Test with gzip at different compression levels
        for level in range(1, 10):
            compressed_file = temp_compression_dir / f"compressed_level_{level}.gz"
            with gzip.open(compressed_file, 'wb', compresslevel=level) as f:
                f.write(original_bytes)
            
            # Decompress
            decompressed_bytes = gzip.open(compressed_file, 'rb').read()
            
            # Verify bitwise equality for all compression levels
            assert original_bytes == decompressed_bytes, \
                f"Gzip level {level} failed bitwise equality"
            
            # Load and verify
            decompressed_file = temp_compression_dir / f"decompressed_level_{level}.json"
            with open(decompressed_file, 'wb') as f:
                f.write(decompressed_bytes)
            
            reconstructed_data, _ = self._load_waveform_from_json(decompressed_file)
            mse = self._compute_mse(sample_waveform_data, reconstructed_data)
            
            # ASSERTION: MSE must be exactly 0 for all compression levels
            assert mse == 0, f"Gzip level {level} failed: MSE = {mse}"

    def test_lossless_compression_with_realistic_gw_data(self, temp_compression_dir):
        """
        Test lossless compression with realistic gravitational wave data characteristics.
        
        Uses data with:
        - High dynamic range (chirp signal)
        - Gaussian noise
        - Float64 precision
        
        Assert: MSE == 0 (bitwise equality)
        """
        # Generate realistic GW-like data
        duration = 8.0
        sample_rate = 8192
        n_samples = int(duration * sample_rate)
        
        t = np.linspace(0, duration, n_samples)
        
        # Chirp signal (inspiral)
        f0 = 20.0
        tau = 4.0
        frequency = f0 * (1 - t/tau)**(-3/8)
        frequency = np.clip(frequency, f0, 1000.0)
        
        amplitude = (1 - t/tau)**(-1/4)
        amplitude = np.clip(amplitude, 0, 50.0)
        
        phase = 2 * np.pi * np.cumsum(frequency) / sample_rate
        strain = amplitude * np.cos(phase)
        
        # Add noise
        noise_std = np.std(strain) / 15.0
        noise = np.random.normal(0, noise_std, n_samples)
        waveform_data = (strain + noise).astype(np.float64)
        
        # Save and compress
        original_file = temp_compression_dir / "gw_original.json"
        self._save_waveform_to_json(waveform_data, original_file)
        
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        # Compress with gzip
        compressed_file = temp_compression_dir / "gw_compressed.gz"
        with gzip.open(compressed_file, 'wb') as f:
            f.write(original_bytes)
        
        # Decompress
        decompressed_bytes = gzip.open(compressed_file, 'rb').read()
        
        # Verify
        assert original_bytes == decompressed_bytes, \
            "Realistic GW data compression failed bitwise equality"
        
        # Load and compute MSE
        decompressed_file = temp_compression_dir / "gw_decompressed.json"
        with open(decompressed_file, 'wb') as f:
            f.write(decompressed_bytes)
        
        reconstructed_data, _ = self._load_waveform_from_json(decompressed_file)
        mse = self._compute_mse(waveform_data, reconstructed_data)
        
        # ASSERTION: MSE must be exactly 0
        assert mse == 0, f"Realistic GW data compression failed: MSE = {mse}"

    def test_compression_ratio_validation(self, sample_waveform_data, temp_compression_dir):
        """
        Verify that lossless compression actually reduces file size.
        
        While not part of the bitwise equality requirement, this ensures
        the compression is working as expected.
        """
        # Save original data
        original_file = temp_compression_dir / "original.json"
        self._save_waveform_to_json(sample_waveform_data, original_file)
        
        original_size = original_file.stat().st_size
        
        # Compress with gzip
        compressed_file = temp_compression_dir / "compressed.gz"
        with open(original_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.write(f_in.read())
        
        compressed_size = compressed_file.stat().st_size
        
        # Verify compression achieved size reduction
        compression_ratio = original_size / compressed_size
        assert compression_ratio > 1.0, \
            f"Compression failed to reduce size: ratio = {compression_ratio}"
        
        # Verify decompressed data still matches
        with gzip.open(compressed_file, 'rb') as f:
            decompressed_bytes = f.read()
        
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        assert original_bytes == decompressed_bytes, \
            "Compressed/decompressed data mismatch"

    def test_multiple_compression_format_interoperability(self, sample_waveform_data, temp_compression_dir):
        """
        Test that data compressed with one format can be decompressed correctly
        and maintains bitwise equality.
        
        Assert: MSE == 0 for each format
        """
        # Save original
        original_file = temp_compression_dir / "original.json"
        self._save_waveform_to_json(sample_waveform_data, original_file)
        
        with open(original_file, 'rb') as f:
            original_bytes = f.read()
        
        # Test gzip
        gzip_file = temp_compression_dir / "test.gz"
        with gzip.open(gzip_file, 'wb') as f:
            f.write(original_bytes)
        decompressed_gzip = gzip.open(gzip_file, 'rb').read()
        assert original_bytes == decompressed_gzip
        
        # Test bzip2
        bzip2_file = temp_compression_dir / "test.bz2"
        with bz2.open(bzip2_file, 'wb') as f:
            f.write(original_bytes)
        decompressed_bzip2 = bz2.open(bzip2_file, 'rb').read()
        assert original_bytes == decompressed_bzip2
        
        # Test lzma
        lzma_file = temp_compression_dir / "test.xz"
        with lzma.open(lzma_file, 'wb') as f:
            f.write(original_bytes)
        decompressed_lzma = lzma.open(lzma_file, 'rb').read()
        assert original_bytes == decompressed_lzma
        
        # Verify all decompressed data matches
        assert decompressed_gzip == decompressed_bzip2 == decompressed_lzma
        
        # Compute MSE for each
        decompressed_file = temp_compression_dir / "decompressed.json"
        
        for name, data in [("gzip", decompressed_gzip), 
                            ("bzip2", decompressed_bzip2), 
                            ("lzma", decompressed_lzma)]:
            with open(decompressed_file, 'wb') as f:
                f.write(data)
            
            reconstructed, _ = self._load_waveform_from_json(decompressed_file)
            mse = self._compute_mse(sample_waveform_data, reconstructed)
            
            # ASSERTION: MSE must be exactly 0 for all formats
            assert mse == 0, f"{name} compression failed: MSE = {mse}"