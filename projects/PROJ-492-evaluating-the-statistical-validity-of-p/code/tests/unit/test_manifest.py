"""
Unit tests for manifest generation utility.
"""
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from code.src.utils.manifest import (
    compute_sha256,
    generate_manifest,
    validate_manifest,
    find_files_to_hash
)

def test_compute_sha256():
    """Test SHA256 computation on a simple file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        temp_path.unlink()

def test_compute_sha256_binary():
    """Test SHA256 computation on a binary file."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        f.write(b"\x00\x01\x02\x03\x04")
        temp_path = Path(f.name)

    try:
        expected_hash = hashlib.sha256(b"\x00\x01\x02\x03\x04").hexdigest()
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        temp_path.unlink()

def test_find_files_to_hash():
    """Test file discovery with exclusions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create some files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_text("cache")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("content3")

        files = find_files_to_hash(tmp_path, exclude_patterns=["__pycache__", ".pyc"])
        
        file_names = [f.name for f in files]
        assert "file1.txt" in file_names
        assert "file2.txt" in file_names
        assert "file3.txt" in file_names
        assert "cache.pyc" not in file_names

def test_generate_manifest():
    """Test manifest generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        data_dir = tmp_path / "data"
        manifest_path = tmp_path / "manifest.json"
        
        output_dir.mkdir()
        data_dir.mkdir()
        
        # Create test files
        (output_dir / "test1.json").write_text('{"key": "value1"}')
        (data_dir / "test2.csv").write_text("a,b,c\n1,2,3")
        
        manifest_data = generate_manifest(output_dir, data_dir, manifest_path)
        
        assert "generated_at" in manifest_data
        assert "version" in manifest_data
        assert "files" in manifest_data
        
        # Check that both files are in the manifest
        assert len(manifest_data["files"]) == 2
        
        # Verify the manifest file was written
        assert manifest_path.exists()
        with open(manifest_path, 'r') as f:
            loaded_manifest = json.load(f)
        assert len(loaded_manifest["files"]) == 2

def test_validate_manifest():
    """Test manifest validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        data_dir = tmp_path / "data"
        manifest_path = tmp_path / "manifest.json"
        
        output_dir.mkdir()
        data_dir.mkdir()
        
        # Create test files
        (output_dir / "test1.json").write_text('{"key": "value1"}')
        
        # Generate manifest
        generate_manifest(output_dir, data_dir, manifest_path)
        
        # Validation should pass
        is_valid, errors = validate_manifest(manifest_path)
        assert is_valid
        assert len(errors) == 0

def test_validate_manifest_missing_file():
    """Test manifest validation with missing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        data_dir = tmp_path / "data"
        manifest_path = tmp_path / "manifest.json"
        
        output_dir.mkdir()
        data_dir.mkdir()
        
        # Create a test file
        (output_dir / "test1.json").write_text('{"key": "value1"}')
        
        # Generate manifest
        generate_manifest(output_dir, data_dir, manifest_path)
        
        # Remove the file
        (output_dir / "test1.json").unlink()
        
        # Validation should fail
        is_valid, errors = validate_manifest(manifest_path)
        assert not is_valid
        assert len(errors) == 1
        assert "missing" in errors[0].lower()

def test_validate_manifest_hash_mismatch():
    """Test manifest validation with hash mismatch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        data_dir = tmp_path / "data"
        manifest_path = tmp_path / "manifest.json"
        
        output_dir.mkdir()
        data_dir.mkdir()
        
        # Create a test file
        test_file = output_dir / "test1.json"
        test_file.write_text('{"key": "value1"}')
        
        # Generate manifest
        generate_manifest(output_dir, data_dir, manifest_path)
        
        # Modify the file
        test_file.write_text('{"key": "modified_value"}')
        
        # Validation should fail
        is_valid, errors = validate_manifest(manifest_path)
        assert not is_valid
        assert len(errors) == 1
        assert "mismatch" in errors[0].lower()

def test_generate_manifest_empty_dirs():
    """Test manifest generation with empty directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "output"
        data_dir = tmp_path / "data"
        manifest_path = tmp_path / "manifest.json"
        
        output_dir.mkdir()
        data_dir.mkdir()
        
        manifest_data = generate_manifest(output_dir, data_dir, manifest_path)
        
        assert len(manifest_data["files"]) == 0
        assert manifest_path.exists()
