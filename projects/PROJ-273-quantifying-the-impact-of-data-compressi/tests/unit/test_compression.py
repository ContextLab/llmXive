"""
Unit tests for lossless compression bitwise equality.

Tests verify that decompressed data matches the original data exactly
(bitwise equality, MSE == 0) for lossless compression algorithms.
"""
import pytest
import os
import sys
import tempfile
import numpy as np
from pathlib import Path

# Add code root to path for imports
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.compression.lossless import compress_gzip, decompress_gzip
from src.compression.lossless import compress_lz4, decompress_lz4
from src.compression.lossless import compress_bzip2, decompress_bzip2
from src.compression.metrics import compute_mse


class TestLosslessCompression:
    """Test suite for lossless compression algorithms."""

    @pytest.fixture
    def sample_waveform(self):
        """Generate a realistic gravitational wave strain waveform."""
        # Simulate a typical GW strain time series
        # Sample rate: 4096 Hz, Duration: 4 seconds
        sample_rate = 4096
        duration = 4
        n_samples = sample_rate * duration
        
        # Generate a chirp-like signal with noise
        t = np.linspace(0, duration, n_samples)
        frequency = 20 + 50 * t  # Frequency sweeps from 20 to 220 Hz
        amplitude = 1e-21 * (1 + 0.5 * np.sin(2 * np.pi * 0.5 * t))
        
        signal = amplitude * np.sin(2 * np.pi * frequency * t)
        noise = np.random.normal(0, 1e-22, n_samples)
        
        waveform = signal + noise
        return waveform.astype(np.float64)

    @pytest.fixture
    def sample_metadata(self):
        """Generate sample metadata for compression test."""
        return {
            "event_id": "GW150914_test",
            "detector": "LIGO_Hanford",
            "sample_rate": 4096,
            "duration": 4.0,
            "compression_type": "lossless"
        }

    def test_gzip_compression_bitwise_equality(self, sample_waveform, sample_metadata):
        """Test that gzip compression/decompression preserves data exactly (MSE == 0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save original data
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            # Compress
            compressed_path = Path(tmpdir) / "compressed.gz"
            compress_gzip(original_path, compressed_path)
            
            # Decompress
            decompressed_path = Path(tmpdir) / "decompressed.npy"
            decompress_gzip(compressed_path, decompressed_path)
            
            # Load and compare
            original_data = np.load(original_path)
            decompressed_data = np.load(decompressed_path)
            
            # Assert bitwise equality
            assert np.array_equal(original_data, decompressed_data), \
                "Gzip compression/decompression failed bitwise equality"
            
            # Assert MSE is exactly 0
            mse = compute_mse(original_data, decompressed_data)
            assert mse == 0.0, f"Gzip MSE should be 0, got {mse}"

    def test_gzip_compression_different_levels(self, sample_waveform):
        """Test gzip compression at different levels (1, 5, 9) all preserve data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            for level in [1, 5, 9]:
                compressed_path = Path(tmpdir) / f"compressed_l{level}.gz"
                decompressed_path = Path(tmpdir) / f"decompressed_l{level}.npy"
                
                compress_gzip(original_path, compressed_path, level=level)
                decompress_gzip(compressed_path, decompressed_path)
                
                original_data = np.load(original_path)
                decompressed_data = np.load(decompressed_path)
                
                mse = compute_mse(original_data, decompressed_data)
                assert mse == 0.0, f"Gzip level {level} failed: MSE = {mse}"

    def test_lz4_compression_bitwise_equality(self, sample_waveform, sample_metadata):
        """Test that lz4 compression/decompression preserves data exactly (MSE == 0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            # Compress
            compressed_path = Path(tmpdir) / "compressed.lz4"
            compress_lz4(original_path, compressed_path)
            
            # Decompress
            decompressed_path = Path(tmpdir) / "decompressed.npy"
            decompress_lz4(compressed_path, decompressed_path)
            
            # Load and compare
            original_data = np.load(original_path)
            decompressed_data = np.load(decompressed_path)
            
            # Assert bitwise equality
            assert np.array_equal(original_data, decompressed_data), \
                "LZ4 compression/decompression failed bitwise equality"
            
            # Assert MSE is exactly 0
            mse = compute_mse(original_data, decompressed_data)
            assert mse == 0.0, f"LZ4 MSE should be 0, got {mse}"

    def test_lz4_compression_different_levels(self, sample_waveform):
        """Test LZ4 compression at different levels (0, 5, 9) all preserve data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            for level in [0, 5, 9]:
                compressed_path = Path(tmpdir) / f"compressed_l{level}.lz4"
                decompressed_path = Path(tmpdir) / f"decompressed_l{level}.npy"
                
                compress_lz4(original_path, compressed_path, level=level)
                decompress_lz4(compressed_path, decompressed_path)
                
                original_data = np.load(original_path)
                decompressed_data = np.load(decompressed_path)
                
                mse = compute_mse(original_data, decompressed_data)
                assert mse == 0.0, f"LZ4 level {level} failed: MSE = {mse}"

    def test_bzip2_compression_bitwise_equality(self, sample_waveform, sample_metadata):
        """Test that bzip2 compression/decompression preserves data exactly (MSE == 0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            # Compress
            compressed_path = Path(tmpdir) / "compressed.bz2"
            compress_bzip2(original_path, compressed_path)
            
            # Decompress
            decompressed_path = Path(tmpdir) / "decompressed.npy"
            decompress_bzip2(compressed_path, decompressed_path)
            
            # Load and compare
            original_data = np.load(original_path)
            decompressed_data = np.load(decompressed_path)
            
            # Assert bitwise equality
            assert np.array_equal(original_data, decompressed_data), \
                "Bzip2 compression/decompression failed bitwise equality"
            
            # Assert MSE is exactly 0
            mse = compute_mse(original_data, decompressed_data)
            assert mse == 0.0, f"Bzip2 MSE should be 0, got {mse}"

    def test_bzip2_compression_different_levels(self, sample_waveform):
        """Test bzip2 compression at different levels (1, 5, 9) all preserve data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            for level in [1, 5, 9]:
                compressed_path = Path(tmpdir) / f"compressed_l{level}.bz2"
                decompressed_path = Path(tmpdir) / f"decompressed_l{level}.npy"
                
                compress_bzip2(original_path, compressed_path, level=level)
                decompress_bzip2(compressed_path, decompressed_path)
                
                original_data = np.load(original_path)
                decompressed_data = np.load(decompressed_path)
                
                mse = compute_mse(original_data, decompressed_data)
                assert mse == 0.0, f"Bzip2 level {level} failed: MSE = {mse}"

    def test_compression_ratio_lossless(self, sample_waveform):
        """Verify that compression actually reduces file size for all algorithms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "original.npy"
            np.save(original_path, sample_waveform)
            
            original_size = original_path.stat().st_size
            
            # Test gzip
            gzip_path = Path(tmpdir) / "test.gz"
            compress_gzip(original_path, gzip_path)
            gzip_size = gzip_path.stat().st_size
            assert gzip_size < original_size, "Gzip should reduce file size"
            
            # Test lz4
            lz4_path = Path(tmpdir) / "test.lz4"
            compress_lz4(original_path, lz4_path)
            lz4_size = lz4_path.stat().st_size
            assert lz4_size < original_size, "LZ4 should reduce file size"
            
            # Test bzip2
            bzip2_path = Path(tmpdir) / "test.bz2"
            compress_bzip2(original_path, bzip2_path)
            bzip2_size = bzip2_path.stat().st_size
            assert bzip2_size < original_size, "Bzip2 should reduce file size"

    def test_invalid_compression_file_handling(self):
        """Test that decompression fails gracefully on invalid files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an invalid compressed file
            invalid_path = Path(tmpdir) / "invalid.gz"
            invalid_path.write_bytes(b"not a valid gzip file")
            
            output_path = Path(tmpdir) / "output.npy"
            
            # Should raise an error when trying to decompress invalid file
            with pytest.raises(Exception):
                decompress_gzip(invalid_path, output_path)

    def test_large_waveform_compression(self):
        """Test compression on a larger waveform (10 seconds)."""
        sample_rate = 16384
        duration = 10
        n_samples = sample_rate * duration
        waveform = np.random.normal(0, 1e-22, n_samples).astype(np.float64)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = Path(tmpdir) / "large_original.npy"
            np.save(original_path, waveform)
            
            compressed_path = Path(tmpdir) / "large_compressed.gz"
            decompressed_path = Path(tmpdir) / "large_decompressed.npy"
            
            compress_gzip(original_path, compressed_path)
            decompress_gzip(compressed_path, decompressed_path)
            
            original_data = np.load(original_path)
            decompressed_data = np.load(decompressed_path)
            
            mse = compute_mse(original_data, decompressed_data)
            assert mse == 0.0, f"Large waveform compression failed: MSE = {mse}"
            assert np.array_equal(original_data, decompressed_data)