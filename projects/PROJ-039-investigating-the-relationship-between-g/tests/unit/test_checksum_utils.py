import os
import tempfile
from pathlib import Path
import pytest
from checksum_utils import compute_checksum, generate_checksums, verify_checksums

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / 'data'
        data_dir.mkdir()
        
        # Create a test file with known content
        test_file = data_dir / 'test.txt'
        test_file.write_text("Hello, World!")
        
        # Create a subdirectory with another file
        subdir = data_dir / 'subdir'
        subdir.mkdir()
        sub_file = subdir / 'nested.txt'
        sub_file.write_text("Nested content")
        
        yield data_dir

def test_compute_checksum(temp_data_dir):
    """Test SHA256 computation on a known file."""
    file_path = temp_data_dir / 'test.txt'
    checksum = compute_checksum(file_path)
    
    # Known SHA256 for "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected

def test_compute_checksum_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_checksum(Path('/nonexistent/file.txt'))

def test_generate_checksums(temp_data_dir):
    """Test generation of checksums for all files in a directory."""
    output_path = Path(temp_data_dir.parent) / 'checksums.txt'
    
    checksums = generate_checksums(temp_data_dir, output_path)
    
    assert len(checksums) == 2
    assert 'test.txt' in checksums
    assert 'subdir/nested.txt' in checksums
    
    # Verify file content
    assert output_path.exists()
    content = output_path.read_text()
    assert 'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f' in content

def test_verify_checksums_success(temp_data_dir):
    """Test successful verification of checksums."""
    output_path = Path(temp_data_dir.parent) / 'checksums.txt'
    generate_checksums(temp_data_dir, output_path)
    
    is_valid, failed = verify_checksums(temp_data_dir, output_path)
    
    assert is_valid is True
    assert len(failed) == 0

def test_verify_checksums_failure(temp_data_dir):
    """Test verification failure when file content changes."""
    output_path = Path(temp_data_dir.parent) / 'checksums.txt'
    generate_checksums(temp_data_dir, output_path)
    
    # Modify a file
    test_file = temp_data_dir / 'test.txt'
    test_file.write_text("Modified content")
    
    is_valid, failed = verify_checksums(temp_data_dir, output_path)
    
    assert is_valid is False
    assert 'test.txt' in failed

def test_verify_checksums_missing_file(temp_data_dir):
    """Test verification failure when a file is missing."""
    output_path = Path(temp_data_dir.parent) / 'checksums.txt'
    generate_checksums(temp_data_dir, output_path)
    
    # Delete a file
    test_file = temp_data_dir / 'test.txt'
    test_file.unlink()
    
    is_valid, failed = verify_checksums(temp_data_dir, output_path)
    
    assert is_valid is False
    assert 'test.txt' in failed
