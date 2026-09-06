import os
import tempfile
import hashlib
from pathlib import Path
import pytest

# Ensure we can import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from checksum_utils import (
    compute_checksum,
    generate_checksums,
    verify_checksums,
    update_checksum_for_file
)
from config import get_project_root

def test_compute_checksum_sha256():
    """Test SHA256 checksum computation."""
    content = b"test data for checksum"
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        expected = hashlib.sha256(content).hexdigest()
        actual = compute_checksum(temp_path, "sha256")
        assert actual == expected
    finally:
        temp_path.unlink()

def test_compute_checksum_md5():
    """Test MD5 checksum computation."""
    content = b"test data for checksum"
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        expected = hashlib.md5(content).hexdigest()
        actual = compute_checksum(temp_path, "md5")
        assert actual == expected
    finally:
        temp_path.unlink()

def test_compute_checksum_nonexistent_file():
    """Test that compute_checksum raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_checksum(Path("/nonexistent/file.txt"))

def test_compute_checksum_invalid_algorithm():
    """Test that compute_checksum raises ValueError for invalid algorithm."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"data")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError):
            compute_checksum(temp_path, "invalid_algo")
    finally:
        temp_path.unlink()

def test_generate_checksums():
    """Test generating checksums for multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        output_file = Path(tmpdir) / "checksums.txt"

        # We need to mock the project root relative path logic or just test the function
        # Since get_project_root() returns the actual repo root, we'll create files there or adjust logic
        # For this unit test, we will test the logic by creating files in the actual artifacts dir or temp dir
        # and ensuring the function handles paths correctly.
        
        # To avoid dependency on project root structure for unit tests, 
        # we will test the core logic by creating files in a temp dir and 
        # verifying the output file content structure.
        
        # Note: The implementation uses relative_to(get_project_root()). 
        # If files are not under project root, this will fail.
        # We will create files in the actual data/processed or similar to ensure it works.
        
        # Alternative: Mock get_project_root? No, let's create real files in the project structure.
        # Since we are in a unit test, we can create a temp dir and mock the function if needed,
        # but simpler is to just ensure the files exist in the project root for the test run.
        
        # Let's create files in the actual project's data/raw or similar if it exists, 
        # or just rely on the fact that the test runner will have the repo structure.
        # To be safe, we'll create files in the temp dir and patch get_project_root.
        
        import checksum_utils
        original_root = checksum_utils.get_project_root
        
        try:
            # Mock get_project_root to return the temp dir
            checksum_utils.get_project_root = lambda: Path(tmpdir)
            
            checksums = generate_checksums([file1, file2], output_file, "sha256")
            
            assert len(checksums) == 2
            assert "file1.txt" in checksums
            assert "file2.txt" in checksums
            
            # Verify file content
            assert output_file.exists()
            content = output_file.read_text()
            assert "file1.txt" in content
            assert "file2.txt" in content
            
            # Verify JSON manifest
            json_manifest = Path(tmpdir) / "checksums_manifest.json"
            assert json_manifest.exists()
        finally:
            checksum_utils.get_project_root = original_root

def test_verify_checksums_success():
    """Test successful verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("content")
        
        output_file = Path(tmpdir) / "checksums.txt"
        
        import checksum_utils
        original_root = checksum_utils.get_project_root
        try:
            checksum_utils.get_project_root = lambda: Path(tmpdir)
            generate_checksums([file1], output_file, "sha256")
            
            valid, passed, failed = verify_checksums(output_file, "sha256")
            
            assert valid is True
            assert len(passed) == 1
            assert len(failed) == 0
        finally:
            checksum_utils.get_project_root = original_root

def test_verify_checksums_failure():
    """Test verification failure due to content change."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("original content")
        
        output_file = Path(tmpdir) / "checksums.txt"
        
        import checksum_utils
        original_root = checksum_utils.get_project_root
        try:
            checksum_utils.get_project_root = lambda: Path(tmpdir)
            generate_checksums([file1], output_file, "sha256")
            
            # Modify file
            file1.write_text("modified content")
            
            valid, passed, failed = verify_checksums(output_file, "sha256")
            
            assert valid is False
            assert len(failed) == 1
        finally:
            checksum_utils.get_project_root = original_root

def test_update_checksum_for_file():
    """Test updating a checksum for a file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("content 1")
        
        output_file = Path(tmpdir) / "checksums.txt"
        
        import checksum_utils
        original_root = checksum_utils.get_project_root
        try:
            checksum_utils.get_project_root = lambda: Path(tmpdir)
            
            # Generate initial checksums
            generate_checksums([file1], output_file, "sha256")
            
            # Change content
            file1.write_text("content 2")
            
            # Update checksum
            success = update_checksum_for_file(file1, output_file, "sha256")
            assert success is True
            
            # Verify updated checksum
            valid, _, _ = verify_checksums(output_file, "sha256")
            assert valid is True
        finally:
            checksum_utils.get_project_root = original_root
