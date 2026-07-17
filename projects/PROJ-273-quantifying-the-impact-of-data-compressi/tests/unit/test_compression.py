"""
Unit tests for lossless compression bitwise equality.

This module verifies that lossless compression algorithms (gzip, LZ4, bzip2)
preserve data exactly when decompressed, satisfying the requirement that
mse == 0 for lossless methods.
"""
import pytest
import numpy as np
import gzip
import bz2
import lz4.frame
import io
import os
import sys
from pathlib import Path

# Add project root to path to import src modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.compression.lossless import compress_gzip, decompress_gzip
from src.compression.lossless import compress_lz4, decompress_lz4
from src.compression.lossless import compress_bzip2, decompress_bzip2


@pytest.fixture
def waveform_data():
    """Generate realistic gravitational wave strain data for testing."""
    # Simulate a short segment of GW strain data (e.g., 1 second at 4096 Hz)
    np.random.seed(42)  # For reproducibility
    duration = 1.0
    sample_rate = 4096
    n_samples = int(duration * sample_rate)
    
    # Generate noise + a simple sine wave (representing a signal)
    t = np.linspace(0, duration, n_samples)
    noise = np.random.normal(0, 1e-21, n_samples)
    signal = 1e-21 * np.sin(2 * np.pi * 100 * t)  # 100 Hz sine wave
    strain = noise + signal
    
    return strain.astype(np.float64)


@pytest.fixture
def compression_levels():
    """Test compression levels 1, 5, and 9 as specified in the project."""
    return [1, 5, 9]


def test_gzip_lossless_bitwise_equality(waveform_data, compression_levels):
    """
    Test that gzip compression/decompression preserves data exactly.
    
    Asserts MSE == 0 between original and decompressed data for all levels.
    """
    for level in compression_levels:
        compressed = compress_gzip(waveform_data, level=level)
        decompressed = decompress_gzip(compressed)
        
        # Verify exact bitwise equality
        assert np.array_equal(waveform_data, decompressed), \
            f"gzip level {level}: Data not preserved exactly"
        
        # Explicit MSE calculation (should be 0.0)
        mse = np.mean((waveform_data - decompressed) ** 2)
        assert mse == 0.0, f"gzip level {level}: MSE = {mse}, expected 0.0"


def test_lz4_lossless_bitwise_equality(waveform_data, compression_levels):
    """
    Test that LZ4 compression/decompression preserves data exactly.
    
    Asserts MSE == 0 between original and decompressed data for all levels.
    """
    for level in compression_levels:
        compressed = compress_lz4(waveform_data, level=level)
        decompressed = decompress_lz4(compressed)
        
        # Verify exact bitwise equality
        assert np.array_equal(waveform_data, decompressed), \
            f"LZ4 level {level}: Data not preserved exactly"
        
        # Explicit MSE calculation (should be 0.0)
        mse = np.mean((waveform_data - decompressed) ** 2)
        assert mse == 0.0, f"LZ4 level {level}: MSE = {mse}, expected 0.0"


def test_bzip2_lossless_bitwise_equality(waveform_data, compression_levels):
    """
    Test that bzip2 compression/decompression preserves data exactly.
    
    Asserts MSE == 0 between original and decompressed data for all levels.
    """
    for level in compression_levels:
        compressed = compress_bzip2(waveform_data, level=level)
        decompressed = decompress_bzip2(compressed)
        
        # Verify exact bitwise equality
        assert np.array_equal(waveform_data, decompressed), \
            f"bzip2 level {level}: Data not preserved exactly"
        
        # Explicit MSE calculation (should be 0.0)
        mse = np.mean((waveform_data - decompressed) ** 2)
        assert mse == 0.0, f"bzip2 level {level}: MSE = {mse}, expected 0.0"


def test_gzip_preserves_dtype(waveform_data):
    """Test that gzip preserves the original data type."""
    compressed = compress_gzip(waveform_data, level=5)
    decompressed = decompress_gzip(compressed)
    assert decompressed.dtype == waveform_data.dtype, \
        f"gzip: dtype changed from {waveform_data.dtype} to {decompressed.dtype}"


def test_lz4_preserves_dtype(waveform_data):
    """Test that LZ4 preserves the original data type."""
    compressed = compress_lz4(waveform_data, level=5)
    decompressed = decompress_lz4(compressed)
    assert decompressed.dtype == waveform_data.dtype, \
        f"LZ4: dtype changed from {waveform_data.dtype} to {decompressed.dtype}"


def test_bzip2_preserves_dtype(waveform_data):
    """Test that bzip2 preserves the original data type."""
    compressed = compress_bzip2(waveform_data, level=5)
    decompressed = decompress_bzip2(compressed)
    assert decompressed.dtype == waveform_data.dtype, \
        f"bzip2: dtype changed from {waveform_data.dtype} to {decompressed.dtype}"


def test_compression_reduces_size(waveform_data):
    """Test that compression actually reduces file size (at least for one level)."""
    original_size = waveform_data.nbytes
    
    # Test with level 9 (maximum compression)
    compressed_gzip = compress_gzip(waveform_data, level=9)
    compressed_lz4 = compress_lz4(waveform_data, level=9)
    compressed_bzip2 = compress_bzip2(waveform_data, level=9)
    
    # At least one method should reduce size
    assert (len(compressed_gzip) < original_size or 
            len(compressed_lz4) < original_size or 
            len(compressed_bzip2) < original_size), \
        "Compression should reduce size for at least one method"


def test_empty_array(waveform_data):
    """Test compression with an empty array."""
    empty_data = np.array([], dtype=np.float64)
    
    # Test gzip
    compressed = compress_gzip(empty_data, level=5)
    decompressed = decompress_gzip(compressed)
    assert np.array_equal(empty_data, decompressed)
    assert mse == 0.0
    
    # Test LZ4
    compressed = compress_lz4(empty_data, level=5)
    decompressed = decompress_lz4(compressed)
    assert np.array_equal(empty_data, decompressed)
    
    # Test bzip2
    compressed = compress_bzip2(empty_data, level=5)
    decompressed = decompress_bzip2(compressed)
    assert np.array_equal(empty_data, decompressed)


def test_single_value(waveform_data):
    """Test compression with a single value."""
    single_value = np.array([1.23456789e-21], dtype=np.float64)
    
    # Test gzip
    compressed = compress_gzip(single_value, level=5)
    decompressed = decompress_gzip(compressed)
    assert np.array_equal(single_value, decompressed)
    assert mse == 0.0
    
    # Test LZ4
    compressed = compress_lz4(single_value, level=5)
    decompressed = decompress_lz4(compressed)
    assert np.array_equal(single_value, decompressed)
    
    # Test bzip2
    compressed = compress_bzip2(single_value, level=5)
    decompressed = decompress_bzip2(compressed)
    assert np.array_equal(single_value, decompressed)


def test_large_array(waveform_data):
    """Test compression with a larger array (10x the size)."""
    large_data = np.tile(waveform_data, 10)
    
    # Test gzip
    compressed = compress_gzip(large_data, level=5)
    decompressed = decompress_gzip(compressed)
    assert np.array_equal(large_data, decompressed)
    assert mse == 0.0
    
    # Test LZ4
    compressed = compress_lz4(large_data, level=5)
    decompressed = decompress_lz4(compressed)
    assert np.array_equal(large_data, decompressed)
    
    # Test bzip2
    compressed = compress_bzip2(large_data, level=5)
    decompressed = decompress_bzip2(compressed)
    assert np.array_equal(large_data, decompressed)


def test_compression_round_trip(waveform_data):
    """Test multiple compression/decompression cycles."""
    current_data = waveform_data.copy()
    
    for _ in range(3):
        # Compress and decompress with each method
        compressed = compress_gzip(current_data, level=5)
        current_data = decompress_gzip(compressed)
        
        compressed = compress_lz4(current_data, level=5)
        current_data = decompress_lz4(compressed)
        
        compressed = compress_bzip2(current_data, level=5)
        current_data = decompress_bzip2(compressed)
    
    # After multiple cycles, data should still be identical
    assert np.array_equal(waveform_data, current_data)
    assert mse == 0.0