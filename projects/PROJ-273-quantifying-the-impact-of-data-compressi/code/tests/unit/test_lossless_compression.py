import pytest
import numpy as np
import tempfile
from pathlib import Path
import json
import os
import sys

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.compression.lossless import (
    compress_gzip, decompress_gzip,
    compress_bzip2, decompress_bzip2,
    compress_lzma, decompress_lzma,
    compress_lz4, decompress_lz4,
    compress_data, decompress_data,
    verify_lossless
)

@pytest.fixture
def sample_data():
    """Generate a simple numpy array for testing."""
    np.random.seed(42)
    return np.random.randn(1000).astype(np.float64)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestGzipCompression:
    def test_compress_gzip_creates_file(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.gz"
        compress_gzip(sample_data, output_path, level=9)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_compress_gzip_decompress_gzip_lossless(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.gz"
        compress_gzip(sample_data, output_path, level=9)
        
        decompressed = decompress_gzip(output_path, shape=sample_data.shape, dtype=sample_data.dtype)
        
        assert np.array_equal(sample_data, decompressed)

    def test_gzip_compression_levels(self, sample_data, temp_output_dir):
        for level in [1, 5, 9]:
            output_path = temp_output_dir / f"test_l{level}.gz"
            _, size = compress_gzip(sample_data, output_path, level=level)
            assert size > 0
            # Higher level should generally result in smaller or equal size
            # (though not strictly guaranteed for all data)

class TestLZMACompression:
    def test_compress_lzma_creates_file(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.xz"
        compress_lzma(sample_data, output_path, preset=6)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_compress_lzma_decompress_lzma_lossless(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.xz"
        compress_lzma(sample_data, output_path, preset=6)
        
        decompressed = decompress_lzma(output_path, shape=sample_data.shape, dtype=sample_data.dtype)
        
        assert np.array_equal(sample_data, decompressed)

class TestBzip2Compression:
    def test_compress_bzip2_creates_file(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.bz2"
        compress_bzip2(sample_data, output_path, level=9)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_compress_bzip2_decompress_bzip2_lossless(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.bz2"
        compress_bzip2(sample_data, output_path, level=9)
        
        decompressed = decompress_bzip2(output_path, shape=sample_data.shape, dtype=sample_data.dtype)
        
        assert np.array_equal(sample_data, decompressed)

class TestCompressData:
    def test_compress_data_dispatch(self, sample_data, temp_output_dir):
        for method in ['gzip', 'bzip2', 'lzma']:
            output_path = compress_data(sample_data, method=method, output_dir=temp_output_dir, filename="test")
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_compress_data_invalid_method(self, sample_data, temp_output_dir):
        with pytest.raises(ValueError, match="Unsupported lossless method"):
            compress_data(sample_data, method="invalid", output_dir=temp_output_dir, filename="test")

class TestDecompressData:
    def test_decompress_data_dispatch(self, sample_data, temp_output_dir):
        for method in ['gzip', 'bzip2', 'lzma']:
            # Compress first
            comp_path = compress_data(sample_data, method=method, output_dir=temp_output_dir, filename="test")
            
            # Decompress
            decomp = decompress_data(comp_path, method=method, shape=sample_data.shape, dtype=sample_data.dtype)
            
            assert np.array_equal(sample_data, decomp)

class TestVerifyLossless:
    def test_verify_lossless_true(self, sample_data, temp_output_dir):
        # Compress and decompress gzip
        comp_path = compress_gzip(sample_data, temp_output_dir / "test.gz", level=9)
        decomp = decompress_gzip(comp_path, shape=sample_data.shape, dtype=sample_data.dtype)
        
        assert verify_lossless(sample_data, decomp)

    def test_verify_lossless_false_shape_mismatch(self, sample_data):
        wrong_shape = np.random.randn(500)
        assert not verify_lossless(sample_data, wrong_shape)

    def test_verify_lossless_false_dtype_mismatch(self, sample_data):
        decomp = sample_data.astype(np.float32)
        # With float32, precision loss might occur, so we expect failure for strict equality
        # unless the data happens to be exactly representable
        # For this test, we just check the function runs and returns False for significant diff
        # or True if by chance it's exact. We'll rely on the tolerance check.
        # A safer test is to manually introduce a difference
        decomp[0] += 1.0
        assert not verify_lossless(sample_data, decomp)

class TestCompressionLevels:
    def test_gzip_level_5_and_9(self, sample_data, temp_output_dir):
        path_5 = compress_gzip(sample_data, temp_output_dir / "l5.gz", level=5)
        path_9 = compress_gzip(sample_data, temp_output_dir / "l9.gz", level=9)
        
        assert path_5.exists()
        assert path_9.exists()
        
        # Verify both are lossless
        d5 = decompress_gzip(path_5, sample_data.shape, sample_data.dtype)
        d9 = decompress_gzip(path_9, sample_data.shape, sample_data.dtype)
        
        assert np.array_equal(sample_data, d5)
        assert np.array_equal(sample_data, d9)

class TestEdgeCases:
    def test_empty_array(self, temp_output_dir):
        empty_data = np.array([])
        comp_path = compress_gzip(empty_data, temp_output_dir / "empty.gz")
        decomp = decompress_gzip(comp_path, shape=empty_data.shape, dtype=empty_data.dtype)
        assert np.array_equal(empty_data, decomp)

    def test_single_element(self, temp_output_dir):
        single = np.array([42.0])
        comp_path = compress_gzip(single, temp_output_dir / "single.gz")
        decomp = decompress_gzip(comp_path, shape=single.shape, dtype=single.dtype)
        assert np.array_equal(single, decomp)
