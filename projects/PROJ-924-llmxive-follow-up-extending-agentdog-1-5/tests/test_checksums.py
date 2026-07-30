import json
import tempfile
from pathlib import Path
import pytest

from checksums_generator import compute_file_checksum, generate_checksums, save_checksums
from utils import load_json_file

@pytest.fixture
def temp_files():
    """Create temporary test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        
        file1.write_text("Hello, World!")
        file2.write_text("Test content for checksum verification.")
        
        yield [file1, file2]

def test_compute_file_checksum(temp_files):
    """Test that compute_file_checksum returns a valid SHA-256 hash."""
    file_path = temp_files[0]
    checksum = compute_file_checksum(file_path)
    
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_generate_checksums(temp_files):
    """Test that generate_checksums creates correct mapping."""
    checksums = generate_checksums(temp_files)
    
    assert len(checksums) == 2
    for path, checksum in checksums.items():
        assert len(checksum) == 64
        # Verify checksum is consistent
        assert compute_file_checksum(Path(path)) == checksum

def test_save_and_load_checksums(temp_files):
    """Test that checksums can be saved and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "checksums.json"
        
        checksums = generate_checksums(temp_files)
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        
        loaded_checksums = load_json_file(output_path)
        assert loaded_checksums == checksums

def test_checksums_for_nonexistent_file():
    """Test that generate_checksums raises error for missing files."""
    fake_path = Path("/nonexistent/file.txt")
    with pytest.raises(FileNotFoundError):
        generate_checksums([fake_path])
