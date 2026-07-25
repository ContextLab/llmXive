"""
Unit tests for checksum functionality.
"""
import pytest
import tempfile
import json
from pathlib import Path
import hashlib

# Import from the project structure
# Assuming tests are run with the project root in sys.path or via pytest
try:
    from data_checksum_manager import compute_file_checksum, record_checksums, save_checksums, load_checksums
except ImportError:
    # Fallback for direct execution if path isn't set
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from data_checksum_manager import compute_file_checksum, record_checksums, save_checksums, load_checksums

def test_checksum_deterministic(tmp_path: Path):
    """Test that checksum is deterministic for the same file content."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    checksum1 = compute_file_checksum(test_file)
    checksum2 = compute_file_checksum(test_file)
    
    assert checksum1 == checksum2
    # Verify it matches the expected SHA256
    expected = hashlib.sha256(content).hexdigest()
    assert checksum1 == expected

def test_checksum_unique(tmp_path: Path):
    """Test that different files have different checksums."""
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    
    file_a.write_bytes(b"Content A")
    file_b.write_bytes(b"Content B")
    
    checksum_a = compute_file_checksum(file_a)
    checksum_b = compute_file_checksum(file_b)
    
    assert checksum_a != checksum_b

def test_record_checksums_structure(tmp_path: Path):
    """Test that record_checksums correctly traverses directories."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    
    (tmp_path / "file1.txt").write_text("data1")
    (subdir / "file2.txt").write_text("data2")
    
    checksums = record_checksums(tmp_path)
    
    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "subdir/file2.txt" in checksums or "subdir\\file2.txt" in checksums

def test_save_load_checksums(tmp_path: Path):
    """Test saving and loading checksums from JSON."""
    data_file = tmp_path / "data.txt"
    data_file.write_text("test content")
    
    checksums = record_checksums(tmp_path)
    output_file = tmp_path / "checksums.json"
    
    save_checksums(checksums, output_file)
    assert output_file.exists()
    
    loaded = load_checksums(output_file)
    assert loaded == checksums