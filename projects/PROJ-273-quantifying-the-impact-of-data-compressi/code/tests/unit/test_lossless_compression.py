"""
Unit tests for lossless compression module.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
import json
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.compression.lossless import (
    compress_gzip, decompress_gzip,
    compress_bzip2, decompress_bzip2,
    compress_lzma, decompress_lzma,
    compress_data, decompress_data,
    verify_lossless
)

@pytest.fixture
def sample_data():
    """Generate sample numpy array for testing."""
    return np.random.randn(1000).astype(np.float64)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestGzipCompression:
    def test_compress_decompress_roundtrip(self, sample_data, temp_output_dir):
        """Test that gzip compression and decompression preserves data."""
        output_path = temp_output_dir / "test.gz"
        
        compress_gzip(sample_data, output_path)
        decompressed = decompress_gzip(output_path)
        
        assert verify_lossless(sample_data, decompressed)

    def test_compression_level_1(self, sample_data, temp_output_dir):
        """Test gzip compression with level 1."""
        output_path = temp_output_dir / "test_l1.gz"
        compress_gzip(sample_data, output_path, level=1)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_compression_level_9(self, sample_data, temp_output_dir):
        """Test gzip compression with level 9."""
        output_path = temp_output_dir / "test_l9.gz"
        compress_gzip(sample_data, output_path, level=9)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

class TestLZMACompression:
    def test_compress_decompress_roundtrip(self, sample_data, temp_output_dir):
        """Test that lzma compression and decompression preserves data."""
        output_path = temp_output_dir / "test.xz"
        
        compress_lzma(sample_data, output_path)
        decompressed = decompress_lzma(output_path)
        
        assert verify_lossless(sample_data, decompressed)

    def test_compression_level_0(self, sample_data, temp_output_dir):
        """Test lzma compression with level 0."""
        output_path = temp_output_dir / "test_l0.xz"
        compress_lzma(sample_data, output_path, level=0)
        
        assert output_path.exists()

    def test_compression_level_9(self, sample_data, temp_output_dir):
        """Test lzma compression with level 9."""
        output_path = temp_output_dir / "test_l9.xz"
        compress_lzma(sample_data, output_path, level=9)
        
        assert output_path.exists()

class TestBzip2Compression:
    def test_compress_decompress_roundtrip(self, sample_data, temp_output_dir):
        """Test that bzip2 compression and decompression preserves data."""
        output_path = temp_output_dir / "test.bz2"
        
        compress_bzip2(sample_data, output_path)
        decompressed = decompress_bzip2(output_path)
        
        assert verify_lossless(sample_data, decompressed)

    def test_compression_level_1(self, sample_data, temp_output_dir):
        """Test bzip2 compression with level 1."""
        output_path = temp_output_dir / "test_l1.bz2"
        compress_bzip2(sample_data, output_path, level=1)
        
        assert output_path.exists()

    def test_compression_level_9(self, sample_data, temp_output_dir):
        """Test bzip2 compression with level 9."""
        output_path = temp_output_dir / "test_l9.bz2"
        compress_bzip2(sample_data, output_path, level=9)
        
        assert output_path.exists()

class TestCompressData:
    def test_dispatch_to_gzip(self, sample_data, temp_output_dir):
        """Test generic compress_data dispatches to gzip."""
        output_path = temp_output_dir / "test.gz"
        compress_data(sample_data, 'gzip', output_path)
        
        assert output_path.exists()

    def test_dispatch_to_bzip2(self, sample_data, temp_output_dir):
        """Test generic compress_data dispatches to bzip2."""
        output_path = temp_output_dir / "test.bz2"
        compress_data(sample_data, 'bzip2', output_path)
        
        assert output_path.exists()

    def test_dispatch_to_lzma(self, sample_data, temp_output_dir):
        """Test generic compress_data dispatches to lzma."""
        output_path = temp_output_dir / "test.xz"
        compress_data(sample_data, 'lzma', output_path)
        
        assert output_path.exists()

    def test_invalid_compression_type(self, sample_data, temp_output_dir):
        """Test that invalid compression type raises error."""
        output_path = temp_output_dir / "test.tmp"
        with pytest.raises(ValueError):
            compress_data(sample_data, 'invalid', output_path)

class TestDecompressData:
    def test_dispatch_to_gzip(self, sample_data, temp_output_dir):
        """Test generic decompress_data dispatches to gzip."""
        output_path = temp_output_dir / "test.gz"
        compress_gzip(sample_data, output_path)
        
        decompressed = decompress_data('gzip', output_path)
        assert verify_lossless(sample_data, decompressed)

    def test_dispatch_to_bzip2(self, sample_data, temp_output_dir):
        """Test generic decompress_data dispatches to bzip2."""
        output_path = temp_output_dir / "test.bz2"
        compress_bzip2(sample_data, output_path)
        
        decompressed = decompress_data('bzip2', output_path)
        assert verify_lossless(sample_data, decompressed)

    def test_dispatch_to_lzma(self, sample_data, temp_output_dir):
        """Test generic decompress_data dispatches to lzma."""
        output_path = temp_output_dir / "test.xz"
        compress_lzma(sample_data, output_path)
        
        decompressed = decompress_data('lzma', output_path)
        assert verify_lossless(sample_data, decompressed)

    def test_invalid_compression_type(self, temp_output_dir):
        """Test that invalid compression type raises error."""
        with pytest.raises(ValueError):
            decompress_data('invalid', temp_output_dir / "test.tmp")

class TestVerifyLossless:
    def test_identical_arrays(self, sample_data):
        """Test verification with identical arrays."""
        assert verify_lossless(sample_data, sample_data.copy())

    def test_different_shapes(self, sample_data):
        """Test verification with different shapes."""
        different_shape = np.random.randn(500).astype(np.float64)
        assert not verify_lossless(sample_data, different_shape)

    def test_different_dtypes(self, sample_data):
        """Test verification with different dtypes."""
        different_dtype = sample_data.astype(np.float32)
        # Should still pass as we convert for comparison
        assert verify_lossless(sample_data, different_dtype)

    def test_tolerance_threshold(self, sample_data):
        """Test verification with tolerance."""
        # Create array with small difference
        noisy = sample_data + np.random.randn(*sample_data.shape) * 1e-15
        assert verify_lossless(sample_data, noisy, tolerance=1e-10)

        # Create array with large difference
        large_diff = sample_data + 1.0
        assert not verify_lossless(sample_data, large_diff, tolerance=1e-10)

class TestCompressionLevels:
    def test_gzip_level_comparison(self, sample_data, temp_output_dir):
        """Test that higher compression levels produce smaller files."""
        path_l1 = temp_output_dir / "test_l1.gz"
        path_l9 = temp_output_dir / "test_l9.gz"
        
        compress_gzip(sample_data, path_l1, level=1)
        compress_gzip(sample_data, path_l9, level=9)
        
        # Level 9 should be smaller or equal to level 1
        assert path_l9.stat().st_size <= path_l1.stat().st_size

    def test_bzip2_level_comparison(self, sample_data, temp_output_dir):
        """Test that higher compression levels produce smaller files."""
        path_l1 = temp_output_dir / "test_l1.bz2"
        path_l9 = temp_output_dir / "test_l9.bz2"
        
        compress_bzip2(sample_data, path_l1, level=1)
        compress_bzip2(sample_data, path_l9, level=9)
        
        assert path_l9.stat().st_size <= path_l1.stat().st_size

class TestEdgeCases:
    def test_empty_array(self, temp_output_dir):
        """Test compression of empty array."""
        empty_data = np.array([]).astype(np.float64)
        output_path = temp_output_dir / "test.gz"
        
        compress_gzip(empty_data, output_path)
        decompressed = decompress_gzip(output_path)
        
        assert len(decompressed) == 0

    def test_single_element(self, temp_output_dir):
        """Test compression of single element array."""
        single_data = np.array([1.0]).astype(np.float64)
        output_path = temp_output_dir / "test.gz"
        
        compress_gzip(single_data, output_path)
        decompressed = decompress_gzip(output_path)
        
        assert verify_lossless(single_data, decompressed)

    def test_large_array(self, temp_output_dir):
        """Test compression of large array."""
        large_data = np.random.randn(1000000).astype(np.float64)
        output_path = temp_output_dir / "test.gz"
        
        compress_gzip(large_data, output_path)
        decompressed = decompress_gzip(output_path)
        
        assert verify_lossless(large_data, decompressed)