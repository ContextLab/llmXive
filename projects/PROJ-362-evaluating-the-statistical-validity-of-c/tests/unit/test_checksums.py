"""
Unit tests for checksum generation functionality.
"""
import os
import json
import hashlib
import tempfile
from pathlib import Path
import pytest

import sys
# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksums import compute_file_checksum, collect_files, generate_checksums_manifest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files with known content."""
    # Create a nested structure
    (temp_dir / "subdir").mkdir()
    
    file1 = temp_dir / "file1.txt"
    file1.write_text("Hello, World!")
    
    file2 = temp_dir / "subdir" / "file2.txt"
    file2.write_text("Test content")
    
    file3 = temp_dir / "file3.csv"
    file3.write_text("a,b,c\n1,2,3")
    
    return [file1, file2, file3]


def test_compute_file_checksum(sample_files):
    """Test SHA-256 checksum computation."""
    file_path = sample_files[0]
    checksum = compute_file_checksum(file_path)
    
    # Verify it's a valid hex string of correct length
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify against known hash
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    assert checksum == expected


def test_compute_file_checksum_nonexistent():
    """Test checksum computation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))


def test_collect_files(temp_dir, sample_files):
    """Test file collection."""
    collected = collect_files(temp_dir)
    
    assert len(collected) == 3
    assert set(collected) == set(sample_files)


def test_collect_files_with_extension_filter(temp_dir, sample_files):
    """Test file collection with extension filter."""
    collected_csv = collect_files(temp_dir, extensions=[".csv"])
    assert len(collected_csv) == 1
    assert collected_csv[0].name == "file3.csv"
    
    collected_txt = collect_files(temp_dir, extensions=[".txt"])
    assert len(collected_txt) == 2


def test_collect_files_empty_directory(temp_dir):
    """Test file collection on empty directory."""
    collected = collect_files(temp_dir)
    assert len(collected) == 0


def test_generate_checksums_manifest(temp_dir, sample_files):
    """Test manifest generation."""
    output_path = temp_dir / "manifest.json"
    
    manifest = generate_checksums_manifest(
        data_dir=temp_dir,
        results_dir=temp_dir,
        output_path=output_path
    )
    
    # Verify manifest structure
    assert "version" in manifest
    assert "algorithm" in manifest
    assert "files" in manifest
    assert manifest["algorithm"] == "SHA-256"
    
    # Verify file entries
    assert len(manifest["files"]) == 3
    
    # Verify manifest file was written
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        loaded_manifest = json.load(f)
        
    assert loaded_manifest == manifest
