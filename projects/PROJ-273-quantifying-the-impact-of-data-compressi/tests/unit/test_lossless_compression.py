"""
Unit tests for lossless compression module.
"""
import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.compression.lossless import (
    compress_gzip,
    decompress_gzip,
    compress_lzma,
    decompress_lzma,
    compress_bzip2,
    decompress_bzip2,
    compress_data,
    decompress_data,
    verify_lossless
)


@pytest.fixture
def sample_data():
    """Create sample strain data for testing."""
    return np.random.randn(10000).astype(np.float64)


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return {
        "event_id": "test_event_001",
        "detector": "LIGO_Hanford",
        "timestamp": 1234567890,
        "sampling_rate": 16384
    }


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_compress_gzip_creates_file(sample_data, sample_metadata, temp_output_dir):
    """Test that gzip compression creates a file."""
    result = compress_gzip(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    assert "path" in result
    assert os.path.exists(result["path"])
    assert result["algorithm"] == "gzip"
    assert result["level"] == 9


def test_decompress_gzip_restores_data(sample_data, sample_metadata, temp_output_dir):
    """Test that gzip decompression restores original data."""
    # Compress
    result = compress_gzip(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    # Decompress
    decompressed_data, metadata = decompress_gzip(result["path"])
    
    # Verify bitwise equality
    assert np.array_equal(sample_data, decompressed_data)
    assert metadata["event_id"] == sample_metadata["event_id"]


def test_compress_lzma_creates_file(sample_data, sample_metadata, temp_output_dir):
    """Test that lzma compression creates a file."""
    result = compress_lzma(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    assert "path" in result
    assert os.path.exists(result["path"])
    assert result["algorithm"] == "lzma"
    assert result["level"] == 9


def test_decompress_lzma_restores_data(sample_data, sample_metadata, temp_output_dir):
    """Test that lzma decompression restores original data."""
    # Compress
    result = compress_lzma(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    # Decompress
    decompressed_data, metadata = decompress_lzma(result["path"])
    
    # Verify bitwise equality
    assert np.array_equal(sample_data, decompressed_data)
    assert metadata["event_id"] == sample_metadata["event_id"]


def test_compress_bzip2_creates_file(sample_data, sample_metadata, temp_output_dir):
    """Test that bzip2 compression creates a file."""
    result = compress_bzip2(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    assert "path" in result
    assert os.path.exists(result["path"])
    assert result["algorithm"] == "bzip2"
    assert result["level"] == 9


def test_decompress_bzip2_restores_data(sample_data, sample_metadata, temp_output_dir):
    """Test that bzip2 decompression restores original data."""
    # Compress
    result = compress_bzip2(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    # Decompress
    decompressed_data, metadata = decompress_bzip2(result["path"])
    
    # Verify bitwise equality
    assert np.array_equal(sample_data, decompressed_data)
    assert metadata["event_id"] == sample_metadata["event_id"]


def test_compress_data_dispatches_correctly(sample_data, sample_metadata, temp_output_dir):
    """Test that compress_data dispatches to the correct algorithm."""
    # Test gzip
    result_gzip = compress_data(sample_data, sample_metadata, "gzip", 5, output_dir=temp_output_dir)
    assert result_gzip["algorithm"] == "gzip"
    
    # Test lzma
    result_lzma = compress_data(sample_data, sample_metadata, "lzma", 5, output_dir=temp_output_dir)
    assert result_lzma["algorithm"] == "lzma"
    
    # Test bzip2
    result_bzip2 = compress_data(sample_data, sample_metadata, "bzip2", 5, output_dir=temp_output_dir)
    assert result_bzip2["algorithm"] == "bzip2"


def test_verify_lossless_returns_true(sample_data, sample_metadata, temp_output_dir):
    """Test that verify_lossless returns True for all algorithms."""
    algorithms = ["gzip", "lzma", "bzip2"]
    
    for algo in algorithms:
        result = compress_data(sample_data, sample_metadata, algo, 9, output_dir=temp_output_dir)
        assert verify_lossless(sample_data, result["path"]), f"Lossless verification failed for {algo}"


def test_different_compression_levels(sample_data, sample_metadata, temp_output_dir):
    """Test that different compression levels produce different file sizes."""
    result_level1 = compress_gzip(sample_data, sample_metadata, level=1, output_dir=temp_output_dir)
    result_level9 = compress_gzip(sample_data, sample_metadata, level=9, output_dir=temp_output_dir)
    
    # Higher compression level should generally produce smaller files
    # (though not always guaranteed for all data types)
    assert result_level1["compressed_size"] >= result_level9["compressed_size"]


def test_invalid_algorithm_raises_error(sample_data, sample_metadata, temp_output_dir):
    """Test that invalid algorithm raises ValueError."""
    with pytest.raises(ValueError):
        compress_data(sample_data, sample_metadata, "invalid_algo", 5, output_dir=temp_output_dir)


def test_decompress_invalid_file_raises_error():
    """Test that decompressing an invalid file raises an error."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"not a compressed file")
        temp_path = f.name
    
    try:
        with pytest.raises(Exception):  # gzip/lzma/bzip2 will raise various exceptions
            decompress_data(temp_path)
    finally:
        os.unlink(temp_path)