"""
Unit tests for lossless compression functionality.

Tests verify that:
1. Compression produces valid output
2. Decompression recovers original data exactly (lossless)
3. Different compression levels work correctly
4. Error handling for invalid inputs
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
import json
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.compression.lossless import (
    compress_gzip, decompress_gzip,
    compress_lzma, decompress_lzma,
    compress_bzip2, decompress_bzip2,
    compress_data, decompress_data,
    verify_lossless,
    COMPRESSION_LEVELS
)

@pytest.fixture
def sample_data():
    """Generate sample strain data for testing."""
    np.random.seed(42)
    return np.random.randn(1024) * 1e-21

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "compressed"
    output_dir.mkdir()
    return output_dir

class TestGzipCompression:
    """Tests for gzip compression."""

    def test_compress_creates_bytes(self, sample_data):
        """Test that compression returns bytes."""
        compressed = compress_gzip(sample_data, level=5)
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_decompress_recovers_original(self, sample_data):
        """Test that decompression recovers original data exactly."""
        compressed = compress_gzip(sample_data, level=9)
        decompressed = decompress_gzip(compressed, sample_data.shape, sample_data.dtype)
        assert np.array_equal(sample_data, decompressed)

    def test_different_levels_produce_different_sizes(self, sample_data):
        """Test that different compression levels produce different sizes."""
        compressed_level5 = compress_gzip(sample_data, level=5)
        compressed_level9 = compress_gzip(sample_data, level=9)
        # Higher compression should produce smaller or equal size
        assert len(compressed_level9) <= len(compressed_level5)

    def test_invalid_level_raises_error(self, sample_data):
        """Test that invalid compression level raises ValueError."""
        with pytest.raises(ValueError):
            compress_gzip(sample_data, level=10)
        with pytest.raises(ValueError):
            compress_gzip(sample_data, level=0)

class TestLZMACompression:
    """Tests for LZMA compression."""

    def test_compress_creates_bytes(self, sample_data):
        """Test that compression returns bytes."""
        compressed = compress_lzma(sample_data, level=5)
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_decompress_recovers_original(self, sample_data):
        """Test that decompression recovers original data exactly."""
        compressed = compress_lzma(sample_data, level=9)
        decompressed = decompress_lzma(compressed, sample_data.shape, sample_data.dtype)
        assert np.array_equal(sample_data, decompressed)

    def test_different_levels_produce_different_sizes(self, sample_data):
        """Test that different compression levels produce different sizes."""
        compressed_level5 = compress_lzma(sample_data, level=5)
        compressed_level9 = compress_lzma(sample_data, level=9)
        # Higher compression should produce smaller or equal size
        assert len(compressed_level9) <= len(compressed_level5)

class TestBzip2Compression:
    """Tests for bzip2 compression."""

    def test_compress_creates_bytes(self, sample_data):
        """Test that compression returns bytes."""
        compressed = compress_bzip2(sample_data, level=5)
        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_decompress_recovers_original(self, sample_data):
        """Test that decompression recovers original data exactly."""
        compressed = compress_bzip2(sample_data, level=9)
        decompressed = decompress_bzip2(compressed, sample_data.shape, sample_data.dtype)
        assert np.array_equal(sample_data, decompressed)

    def test_invalid_level_raises_error(self, sample_data):
        """Test that invalid compression level raises ValueError."""
        with pytest.raises(ValueError):
            compress_bzip2(sample_data, level=10)
        with pytest.raises(ValueError):
            compress_bzip2(sample_data, level=0)

class TestCompressData:
    """Tests for the high-level compress_data function."""

    def test_compress_data_creates_files(self, sample_data, temp_output_dir):
        """Test that compress_data creates output files."""
        result = compress_data(
            data=sample_data,
            method='gzip',
            level=5,
            output_dir=temp_output_dir,
            event_id='test_event',
            metadata={'test': True}
        )
        
        assert 'path' in result
        assert Path(result['path']).exists()
        assert result['original_size_bytes'] == sample_data.nbytes
        assert result['compressed_size_bytes'] > 0
        assert result['compression_ratio'] >= 1.0

    def test_compress_data_with_different_methods(self, sample_data, temp_output_dir):
        """Test compression with all supported methods."""
        for method in ['gzip', 'lzma', 'bzip2']:
            result = compress_data(
                data=sample_data,
                method=method,
                level=5,
                output_dir=temp_output_dir,
                event_id='test_event',
                metadata={'method': method}
            )
            assert Path(result['path']).exists()
            assert result['method'] == method

    def test_compress_data_saves_metadata(self, sample_data, temp_output_dir):
        """Test that metadata is saved correctly."""
        metadata = {'event_id': 'test', 'custom_field': 123}
        result = compress_data(
            data=sample_data,
            method='gzip',
            level=5,
            output_dir=temp_output_dir,
            event_id='test_event',
            metadata=metadata
        )
        
        # Check that metadata file was created
        meta_path = Path(result['path'].replace('.gz', '_meta.json'))
        assert meta_path.exists()
        
        with open(meta_path, 'r') as f:
            saved_meta = json.load(f)
        
        assert saved_meta['metadata']['custom_field'] == 123

    def test_compress_data_verification(self, sample_data, temp_output_dir):
        """Test that compressed data is verified as lossless."""
        result = compress_data(
            data=sample_data,
            method='gzip',
            level=9,
            output_dir=temp_output_dir,
            event_id='test_event'
        )
        
        # Verify the result
        compressed_path = Path(result['path'])
        decompressed = decompress_data(
            compressed_path=compressed_path,
            shape=sample_data.shape,
            dtype=sample_data.dtype,
            method='gzip'
        )
        assert np.array_equal(sample_data, decompressed)

class TestDecompressData:
    """Tests for the high-level decompress_data function."""

    def test_decompress_data_recovers_original(self, sample_data, temp_output_dir):
        """Test that decompress_data recovers original data."""
        # First compress
        compress_data(
            data=sample_data,
            method='gzip',
            level=5,
            output_dir=temp_output_dir,
            event_id='test_event'
        )
        
        # Then decompress
        compressed_path = temp_output_dir / "test_event_gzip_level5.gz"
        decompressed = decompress_data(
            compressed_path=compressed_path,
            shape=sample_data.shape,
            dtype=sample_data.dtype,
            method='gzip'
        )
        
        assert np.array_equal(sample_data, decompressed)

    def test_decompress_data_auto_detect_method(self, sample_data, temp_output_dir):
        """Test that decompress_data can auto-detect compression method."""
        # Create files with different extensions
        for method, ext in [('gzip', '.gz'), ('lzma', '.xz'), ('bzip2', '.bz2')]:
            compress_data(
                data=sample_data,
                method=method,
                level=5,
                output_dir=temp_output_dir,
                event_id=f'test_{method}'
            )
        
        # Decompress without specifying method
        for method, ext in [('gzip', '.gz'), ('lzma', '.xz'), ('bzip2', '.bz2')]:
            compressed_path = temp_output_dir / f"test_{method}_{method}_level5{ext}"
            decompressed = decompress_data(
                compressed_path=compressed_path,
                shape=sample_data.shape,
                dtype=sample_data.dtype
            )
            assert np.array_equal(sample_data, decompressed)

class TestVerifyLossless:
    """Tests for the verify_lossless function."""

    def test_verify_lossless_passes(self, sample_data):
        """Test that verify_lossless returns True for valid compression."""
        for method in ['gzip', 'lzma', 'bzip2']:
            if method == 'gzip':
                compressed = compress_gzip(sample_data, level=5)
            elif method == 'lzma':
                compressed = compress_lzma(sample_data, level=5)
            else:
                compressed = compress_bzip2(sample_data, level=5)
            
            assert verify_lossless(sample_data, compressed, method)

    def test_verify_lossless_with_tolerance(self, sample_data):
        """Test that verify_lossless works with numerical tolerance."""
        compressed = compress_gzip(sample_data, level=5)
        # Should pass with zero tolerance
        assert verify_lossless(sample_data, compressed, 'gzip', tolerance=0.0)

class TestCompressionLevels:
    """Tests for compression level constants."""

    def test_levels_defined(self):
        """Test that compression levels are properly defined."""
        assert 'gzip' in COMPRESSION_LEVELS
        assert 'lzma' in COMPRESSION_LEVELS
        assert 'bzip2' in COMPRESSION_LEVELS
        
        assert 5 in COMPRESSION_LEVELS['gzip']
        assert 9 in COMPRESSION_LEVELS['gzip']
        assert 5 in COMPRESSION_LEVELS['lzma']
        assert 9 in COMPRESSION_LEVELS['lzma']
        assert 5 in COMPRESSION_LEVELS['bzip2']
        assert 9 in COMPRESSION_LEVELS['bzip2']

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_array(self, temp_output_dir):
        """Test compression of empty array."""
        empty_data = np.array([])
        result = compress_data(
            data=empty_data,
            method='gzip',
            level=5,
            output_dir=temp_output_dir,
            event_id='empty_test'
        )
        
        assert result['original_size_bytes'] == 0
        assert Path(result['path']).exists()

    def test_single_element(self, temp_output_dir):
        """Test compression of single element array."""
        single_data = np.array([1.0e-21])
        result = compress_data(
            data=single_data,
            method='gzip',
            level=5,
            output_dir=temp_output_dir,
            event_id='single_test'
        )
        
        compressed_path = Path(result['path'])
        decompressed = decompress_data(
            compressed_path=compressed_path,
            shape=single_data.shape,
            dtype=single_data.dtype
        )
        assert np.array_equal(single_data, decompressed)

    def test_large_array(self, temp_output_dir):
        """Test compression of large array."""
        large_data = np.random.randn(1000000) * 1e-21
        result = compress_data(
            data=large_data,
            method='gzip',
            level=5,
            output_dir=temp_output_dir,
            event_id='large_test'
        )
        
        compressed_path = Path(result['path'])
        decompressed = decompress_data(
            compressed_path=compressed_path,
            shape=large_data.shape,
            dtype=large_data.dtype
        )
        assert np.array_equal(large_data, decompressed)