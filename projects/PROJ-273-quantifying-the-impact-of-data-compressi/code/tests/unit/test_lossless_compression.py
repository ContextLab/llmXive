"""
Unit tests for lossless compression modules.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
import json
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.compression.lossless import (
    compress_gzip, decompress_gzip,
    compress_bzip2, decompress_bzip2,
    compress_lzma, decompress_lzma,
    compress_lz4, decompress_lz4,
    compress_data, decompress_data,
    verify_lossless
)
from src.utils.config import get_project_root, ensure_dir

@pytest.fixture
def sample_data():
    """Generate sample waveform data."""
    return np.random.randn(10000).astype(np.float64)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestGzipCompression:
    def test_compress_gzip_creates_file(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.gz"
        result_path = compress_gzip(sample_data, level=1, output_path=output_path)
        assert result_path.exists()
        assert result_path.suffix == ".gz"

    def test_compress_decompress_roundtrip(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.gz"
        compress_gzip(sample_data, level=1, output_path=output_path)
        decompressed = decompress_gzip(output_path)
        assert np.array_equal(sample_data, decompressed)

    def test_verify_lossless_gzip(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.gz"
        compress_gzip(sample_data, level=1, output_path=output_path)
        decompressed = decompress_gzip(output_path)
        assert verify_lossless(sample_data, decompressed)

    def test_invalid_gzip_level(self, sample_data):
        with pytest.raises(ValueError):
            compress_gzip(sample_data, level=5) # 5 is valid, but let's test 10
        with pytest.raises(ValueError):
            compress_gzip(sample_data, level=10)

class TestLZMACompression:
    def test_compress_lzma_creates_file(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.xz"
        result_path = compress_lzma(sample_data, level=1, output_path=output_path)
        assert result_path.exists()
        assert result_path.suffix == ".xz"

    def test_compress_decompress_roundtrip(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.xz"
        compress_lzma(sample_data, level=1, output_path=output_path)
        decompressed = decompress_lzma(output_path)
        assert np.array_equal(sample_data, decompressed)

    def test_verify_lossless_lzma(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.xz"
        compress_lzma(sample_data, level=1, output_path=output_path)
        decompressed = decompress_lzma(output_path)
        assert verify_lossless(sample_data, decompressed)

class TestBzip2Compression:
    def test_compress_bzip2_creates_file(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.bz2"
        result_path = compress_bzip2(sample_data, level=1, output_path=output_path)
        assert result_path.exists()
        assert result_path.suffix == ".bz2"

    def test_compress_decompress_roundtrip(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.bz2"
        compress_bzip2(sample_data, level=1, output_path=output_path)
        decompressed = decompress_bzip2(output_path)
        assert np.array_equal(sample_data, decompressed)

    def test_verify_lossless_bzip2(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.bz2"
        compress_bzip2(sample_data, level=1, output_path=output_path)
        decompressed = decompress_bzip2(output_path)
        assert verify_lossless(sample_data, decompressed)

class TestCompressData:
    def test_compress_data_dispatcher_gzip(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.gz"
        result_path = compress_data(sample_data, 'gzip', 1, output_path)
        assert result_path.exists()
        decompressed = decompress_data(result_path, 'gzip')
        assert np.array_equal(sample_data, decompressed)

    def test_compress_data_dispatcher_bzip2(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.bz2"
        result_path = compress_data(sample_data, 'bzip2', 1, output_path)
        assert result_path.exists()
        decompressed = decompress_data(result_path, 'bzip2')
        assert np.array_equal(sample_data, decompressed)

    def test_compress_data_dispatcher_lzma(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.xz"
        result_path = compress_data(sample_data, 'lzma', 1, output_path)
        assert result_path.exists()
        decompressed = decompress_data(result_path, 'lzma')
        assert np.array_equal(sample_data, decompressed)

class TestDecompressData:
    def test_decompress_data_dispatcher(self, sample_data, temp_output_dir):
        output_path = temp_output_dir / "test.npy.gz"
        compress_gzip(sample_data, level=1, output_path=output_path)
        decompressed = decompress_data(output_path, 'gzip')
        assert np.array_equal(sample_data, decompressed)

class TestVerifyLossless:
    def test_verify_lossless_true(self, sample_data):
        assert verify_lossless(sample_data, sample_data)

    def test_verify_lossless_false(self, sample_data):
        modified_data = sample_data + 0.1
        assert not verify_lossless(sample_data, modified_data)

    def test_verify_lossless_shape_mismatch(self, sample_data):
        different_shape = np.random.randn(5000).astype(np.float64)
        assert not verify_lossless(sample_data, different_shape)

class TestCompressionLevels:
    @pytest.mark.parametrize("method", ['gzip', 'bzip2', 'lzma'])
    @pytest.mark.parametrize("level", [1, 5, 9])
    def test_all_levels_valid(self, sample_data, temp_output_dir, method, level):
        if method == 'gzip':
            compress_func = compress_gzip
        elif method == 'bzip2':
            compress_func = compress_bzip2
        else:
            compress_func = compress_lzma
        
        output_path = temp_output_dir / f"test_{method}_{level}.tmp"
        result_path = compress_func(sample_data, level=level, output_path=output_path)
        assert result_path.exists()
        
        # Decompress and verify
        if method == 'gzip':
            dec_func = decompress_gzip
        elif method == 'bzip2':
            dec_func = decompress_bzip2
        else:
            dec_func = decompress_lzma
        
        decompressed = dec_func(result_path)
        assert np.array_equal(sample_data, decompressed)

class TestEdgeCases:
    def test_empty_array(self, temp_output_dir):
        empty_data = np.array([], dtype=np.float64)
        output_path = temp_output_dir / "empty.npy.gz"
        compress_gzip(empty_data, level=1, output_path=output_path)
        decompressed = decompress_gzip(output_path)
        assert np.array_equal(empty_data, decompressed)

    def test_single_element(self, temp_output_dir):
        single_data = np.array([1.0], dtype=np.float64)
        output_path = temp_output_dir / "single.npy.gz"
        compress_gzip(single_data, level=1, output_path=output_path)
        decompressed = decompress_gzip(output_path)
        assert np.array_equal(single_data, decompressed)

    def test_large_array(self, temp_output_dir):
        large_data = np.random.randn(1000000).astype(np.float64)
        output_path = temp_output_dir / "large.npy.gz"
        compress_gzip(large_data, level=1, output_path=output_path)
        decompressed = decompress_gzip(output_path)
        assert np.array_equal(large_data, decompressed)