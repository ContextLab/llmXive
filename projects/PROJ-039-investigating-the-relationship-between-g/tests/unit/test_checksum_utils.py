import os
import tempfile
import pytest
from pathlib import Path
from checksum_utils import compute_checksum, generate_checksums, verify_checksums

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir)
        # Create a test file with known content
        test_file = data_path / 'test.txt'
        test_file.write_text("Hello, World!")
        yield data_path

def test_compute_checksum_known_value(temp_dir):
    """Test checksum computation against a known string."""
    file_path = temp_dir / 'test.txt'
    checksum = compute_checksum(file_path)
    # SHA256 of "Hello, World!"
    expected = "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5"
    assert checksum == expected

def test_compute_checksum_nonexistent_file():
    """Test that compute_checksum raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_checksum(Path("/nonexistent/file.txt"))

def test_generate_checksums_creates_file(temp_dir):
    """Test that generate_checksums creates the output file."""
    output_path = temp_dir / 'checksums.txt'
    generate_checksums(temp_dir, output_path)
    assert output_path.exists()
    content = output_path.read_text()
    assert 'test.txt' in content
    assert len(content) > 0

def test_verify_checksums_success(temp_dir):
    """Test successful verification."""
    output_path = temp_dir / 'checksums.txt'
    generate_checksums(temp_dir, output_path)
    
    is_valid, failed = verify_checksums(temp_dir, output_path)
    assert is_valid is True
    assert len(failed) == 0

def test_verify_checksums_failure(temp_dir):
    """Test verification failure when file is modified."""
    output_path = temp_dir / 'checksums.txt'
    generate_checksums(temp_dir, output_path)
    
    # Modify the file
    test_file = temp_dir / 'test.txt'
    test_file.write_text("Modified content")
    
    is_valid, failed = verify_checksums(temp_dir, output_path)
    assert is_valid is False
    assert len(failed) == 1
    assert 'test.txt' in failed[0]

def test_verify_checksums_missing_file(temp_dir):
    """Test verification failure when file is deleted."""
    output_path = temp_dir / 'checksums.txt'
    generate_checksums(temp_dir, output_path)
    
    # Delete the file
    test_file = temp_dir / 'test.txt'
    test_file.unlink()
    
    is_valid, failed = verify_checksums(temp_dir, output_path)
    assert is_valid is False
    assert len(failed) == 1