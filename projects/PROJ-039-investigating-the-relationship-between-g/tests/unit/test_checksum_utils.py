import os
import tempfile
import hashlib
from pathlib import Path
import pytest
from checksum_utils import compute_checksum, generate_checksums, verify_checksums

def test_compute_checksum_file_exists():
    """Test that compute_checksum works on an existing file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Hello, World!")
        temp_path = f.name
    
    try:
        checksum = compute_checksum(temp_path)
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_checksum_file_not_found():
    """Test that compute_checksum raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_checksum("/nonexistent/path/file.txt")

def test_compute_checksum_unsupported_algorithm():
    """Test that compute_checksum raises ValueError for unsupported algorithm."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            compute_checksum(temp_path, algorithm='invalid_algo')
    finally:
        os.unlink(temp_path)

def test_generate_checksums():
    """Test generate_checksums creates correct output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("content1")
        
        file2 = Path(tmpdir) / "subdir" / "file2.txt"
        file2.parent.mkdir(parents=True, exist_ok=True)
        file2.write_text("content2")
        
        output_path = Path(tmpdir) / "checksums.txt"
        
        checksums = generate_checksums(tmpdir, str(output_path))
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify checksums dictionary
        assert len(checksums) == 2
        assert any("file1.txt" in k for k in checksums.keys())
        assert any("file2.txt" in k for k in checksums.keys())
        
        # Verify content of file
        with open(output_path, 'r') as f:
            content = f.read()
            assert "file1.txt" in content
            assert "file2.txt" in content

def test_verify_checksums_success():
    """Test verify_checksums returns True when all checksums match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")
        
        # Generate checksums
        checksum_file = Path(tmpdir) / "checksums.txt"
        generate_checksums(tmpdir, str(checksum_file))
        
        # Verify
        valid, failed = verify_checksums(str(checksum_file), tmpdir)
        assert valid is True
        assert len(failed) == 0

def test_verify_checksums_failure():
    """Test verify_checksums returns False when checksums mismatch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")
        
        # Generate checksums
        checksum_file = Path(tmpdir) / "checksums.txt"
        generate_checksums(tmpdir, str(checksum_file))
        
        # Modify file
        file_path.write_text("modified content")
        
        # Verify should fail
        valid, failed = verify_checksums(str(checksum_file), tmpdir)
        assert valid is False
        assert len(failed) == 1

def test_verify_checksums_missing_file():
    """Test verify_checksums handles missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")
        
        # Generate checksums
        checksum_file = Path(tmpdir) / "checksums.txt"
        generate_checksums(tmpdir, str(checksum_file))
        
        # Delete file
        file_path.unlink()
        
        # Verify should fail
        valid, failed = verify_checksums(str(checksum_file), tmpdir)
        assert valid is False
        assert len(failed) == 1