"""
Tests for the data_integrity module.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from code.data_integrity import (
    compute_file_sha256,
    generate_checksums_for_raw_data,
    save_checksums,
    verify_checksums,
    main
)

def create_temp_file(content: bytes, directory: Path, filename: str) -> Path:
    """Helper to create a temporary file with specific content."""
    file_path = directory / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path

def test_compute_file_sha256():
    """Test SHA-256 computation for a known string."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        content = b"Hello, World!"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        file_path = create_temp_file(content, tmp_path, "test.txt")
        actual_hash = compute_file_sha256(file_path)
        
        assert actual_hash == expected_hash

def test_compute_file_sha256_missing_file():
    """Test that FileNotFoundError is raised for missing files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = Path(tmp_dir) / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_sha256(file_path)

def test_generate_checksums_for_raw_data():
    """Test generation of checksums for multiple files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test files
        content1 = b"Data file 1"
        content2 = b"Data file 2"
        content3 = b"Nested data"
        
        create_temp_file(content1, tmp_path, "file1.csv")
        create_temp_file(content2, tmp_path, "file2.csv")
        create_temp_file(content3, tmp_path / "subdir", "file3.csv")
        
        checksums = generate_checksums_for_raw_data(tmp_path)
        
        assert len(checksums) == 3
        assert "file1.csv" in checksums
        assert "file2.csv" in checksums
        assert "subdir/file3.csv" in checksums
        
        # Verify one hash manually
        expected_hash1 = hashlib.sha256(content1).hexdigest()
        assert checksums["file1.csv"] == expected_hash1

def test_save_and_verify_checksums():
    """Test saving checksums to JSON and verifying them."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test file
        content = b"Verify me"
        file_path = create_temp_file(content, tmp_path, "verify.csv")
        
        # Generate and save checksums
        checksums = generate_checksums_for_raw_data(tmp_path)
        output_path = tmp_path / "checksums.json"
        save_checksums(checksums, output_path)
        
        assert output_path.exists()
        
        # Verify checksums
        results = verify_checksums(tmp_path, output_path)
        
        assert len(results) == 1
        assert results["verify.csv"] is True

def test_verify_checksums_modified_file():
    """Test that verification fails for a modified file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create and save original file
        original_content = b"Original content"
        file_path = create_temp_file(original_content, tmp_path, "modified.csv")
        
        checksums = generate_checksums_for_raw_data(tmp_path)
        output_path = tmp_path / "checksums.json"
        save_checksums(checksums, output_path)
        
        # Modify the file
        with open(file_path, "wb") as f:
            f.write(b"Modified content")
        
        # Verify should fail
        results = verify_checksums(tmp_path, output_path)
        
        assert results["modified.csv"] is False

def test_verify_checksums_missing_file():
    """Test that verification fails for a missing file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create file and save checksums
        content = b"Missing file test"
        create_temp_file(content, tmp_path, "gone.csv")
        
        checksums = generate_checksums_for_raw_data(tmp_path)
        output_path = tmp_path / "checksums.json"
        save_checksums(checksums, output_path)
        
        # Delete the file
        (tmp_path / "gone.csv").unlink()
        
        # Verify should fail
        results = verify_checksums(tmp_path, output_path)
        
        assert results["gone.csv"] is False

def test_generate_checksums_empty_directory():
    """Test checksum generation on an empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        checksums = generate_checksums_for_raw_data(tmp_path)
        assert checksums == {}

def test_main_generate(capsys):
    """Test main function in generate mode."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        create_temp_file(b"Test data", tmp_path, "test.csv")
        
        output_json = tmp_path / "checksums.json"
        
        # Mock args for generate mode
        import sys
        original_argv = sys.argv
        sys.argv = ["test", "--raw-dir", str(tmp_path), "--checksums-file", str(output_json)]
        
        try:
            result = main()
            assert result == 0
            assert output_json.exists()
        finally:
            sys.argv = original_argv

def test_main_verify(capsys):
    """Test main function in verify mode."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        create_temp_file(b"Test data", tmp_path, "test.csv")
        
        output_json = tmp_path / "checksums.json"
        
        # Generate first
        import sys
        original_argv = sys.argv
        sys.argv = ["test", "--raw-dir", str(tmp_path), "--checksums-file", str(output_json)]
        main()
        
        # Now verify
        sys.argv = ["test", "--verify", "--raw-dir", str(tmp_path), "--checksums-file", str(output_json)]
        try:
            result = main()
            assert result == 0
        finally:
            sys.argv = original_argv
