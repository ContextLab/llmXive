"""
Unit tests for cleanup_intermediates.py (Task T021)
"""
import os
import gzip
import shutil
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.cleanup_intermediates import (
    get_directory_size,
    get_large_files,
    compress_file,
    remove_intermediate_file,
    identify_intermediate_files,
    cleanup_pipeline
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create subdirectories
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "metrics").mkdir()
    
    # Create some test files
    large_file = data_dir / "raw" / "large_file.nii"
    large_file.write_bytes(b'x' * 200 * 1024 * 1024)  # 200MB
    
    small_file = data_dir / "raw" / "small_file.nii"
    small_file.write_bytes(b'y' * 50 * 1024 * 1024)  # 50MB
    
    log_file = data_dir / "raw" / "processing.log"
    log_file.write_bytes(b'z' * 150 * 1024 * 1024)  # 150MB
    
    temp_file = data_dir / "raw" / "temp_file.tmp"
    temp_file.write_bytes(b'a' * 10 * 1024 * 1024)  # 10MB
    
    # Create a processed file to mark the raw file as "processed"
    processed_file = data_dir / "processed" / "large_file.nii.gz"
    processed_file.write_bytes(b'b' * 10 * 1024 * 1024)  # 10MB
    
    return data_dir

def test_get_directory_size(temp_data_dir):
    """Test directory size calculation."""
    size = get_directory_size(temp_data_dir)
    expected_size = (200 + 50 + 150 + 10 + 10) * 1024 * 1024
    assert size == expected_size

def test_get_large_files(temp_data_dir):
    """Test finding large files."""
    large_files = get_large_files(temp_data_dir, threshold=100 * 1024 * 1024)
    assert len(large_files) == 3  # large_file.nii, log_file, and processed_file
    
    # Check they are sorted by size
    sizes = [size for _, size in large_files]
    assert sizes == sorted(sizes, reverse=True)

def test_compress_file(temp_data_dir):
    """Test file compression."""
    test_file = temp_data_dir / "raw" / "small_file.nii"
    assert test_file.exists()
    
    result = compress_file(test_file)
    assert result is True
    assert test_file.exists() is False
    assert (temp_data_dir / "raw" / "small_file.nii.gz").exists()

def test_remove_intermediate_file(temp_data_dir):
    """Test file removal."""
    test_file = temp_data_dir / "raw" / "temp_file.tmp"
    assert test_file.exists()
    
    result = remove_intermediate_file(test_file)
    assert result is True
    assert test_file.exists() is False

def test_identify_intermediate_files(temp_data_dir):
    """Test identification of intermediate files."""
    intermediate = identify_intermediate_files(temp_data_dir)
    
    # Should include large_file.nii (processed exists) and log_file
    file_names = [f.name for f in intermediate]
    assert "large_file.nii" in file_names
    assert "processing.log" in file_names
    assert "temp_file.tmp" in file_names

def test_cleanup_pipeline(temp_data_dir, monkeypatch):
    """Test the full cleanup pipeline."""
    # Mock the MAX_SIZE_BYTES to force cleanup
    from data import cleanup_intermediates
    original_max = cleanup_intermediates.MAX_SIZE_BYTES
    cleanup_intermediates.MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100MB limit
    
    try:
        stats = cleanup_pipeline()
        
        assert stats['files_compressed'] > 0 or stats['files_removed'] > 0
        assert stats['final_size_bytes'] <= cleanup_intermediates.MAX_SIZE_BYTES
    finally:
        cleanup_intermediates.MAX_SIZE_BYTES = original_max

def test_nonexistent_directory():
    """Test handling of non-existent directory."""
    size = get_directory_size(Path("/nonexistent/path"))
    assert size == 0
    
    large_files = get_large_files(Path("/nonexistent/path"))
    assert len(large_files) == 0
    
    intermediate = identify_intermediate_files(Path("/nonexistent/path"))
    assert len(intermediate) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])