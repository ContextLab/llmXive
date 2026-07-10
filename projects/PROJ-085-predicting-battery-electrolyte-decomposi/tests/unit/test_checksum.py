import pytest
import tempfile
import json
from pathlib import Path
import hashlib

from code.data.checksum import (
    compute_sha256,
    save_checksums,
    load_checksums,
    validate_file,
    validate_all_checksums,
    register_file
)
from code.data.structure import get_project_root


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_compute_sha256(temp_file):
    """Test SHA-256 computation on a known file."""
    checksum = compute_sha256(temp_file)
    assert len(checksum) == 64  # SHA-256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify against known value
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    assert checksum == expected


def test_compute_sha256_nonexistent():
    """Test that compute_sha256 raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))


def test_save_and_load_checksums(temp_dir):
    """Test saving and loading checksums."""
    checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456"
    }
    
    output_path = temp_dir / "checksums.json"
    save_checksums(checksums, output_path)
    
    loaded = load_checksums(output_path)
    assert loaded == checksums


def test_validate_file(temp_file):
    """Test file validation with correct and incorrect checksums."""
    checksum = compute_sha256(temp_file)
    
    # Valid checksum
    assert validate_file(temp_file, checksum) is True
    
    # Invalid checksum
    assert validate_file(temp_file, "wrong_checksum") is False


def test_validate_file_nonexistent():
    """Test validation of non-existent file."""
    assert validate_file(Path("/nonexistent/file.txt"), "abc123") is False


def test_register_file(temp_file, temp_dir):
    """Test registering a file's checksum."""
    checksums = {}
    result = register_file(temp_file, checksums)
    
    assert len(result) == 1
    assert temp_file.name in str(list(result.keys())[0])
    assert result[str(temp_file)] == compute_sha256(temp_file)


def test_validate_all_checksums(temp_dir):
    """Test validating all checksums from a file."""
    # Create test files
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"
    file1.write_text("Content 1")
    file2.write_text("Content 2")
    
    # Create checksums file
    checksums = {
        str(file1): compute_sha256(file1),
        str(file2): compute_sha256(file2)
    }
    
    checksums_file = temp_dir / "checksums.json"
    save_checksums(checksums, checksums_file)
    
    # Temporarily change project root for testing
    # Note: This is a simplified test; in real usage, validate_all_checksums
    # would use the actual project root
    import code.data.checksum as checksum_module
    original_get_project_root = checksum_module.get_project_root
    
    def mock_get_project_root():
        return temp_dir
    
    checksum_module.get_project_root = mock_get_project_root
    
    try:
        results = validate_all_checksums()
        assert len(results) == 2
        assert results[str(file1)] is True
        assert results[str(file2)] is True
    finally:
        checksum_module.get_project_root = original_get_project_root
