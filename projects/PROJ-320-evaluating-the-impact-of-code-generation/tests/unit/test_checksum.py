"""
Unit tests for checksum utilities.
"""
import json
import tempfile
import os
from pathlib import Path
import pytest

from code.utils.checksum import (
    calculate_checksum,
    verify_checksum,
    generate_checksum_manifest,
    load_checksum_manifest
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write('{"test": "data", "number": 123}')
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_calculate_checksum_returns_hex_string(temp_file):
    """Test that calculate_checksum returns a 64-character hex string."""
    checksum = calculate_checksum(temp_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum.lower())

def test_calculate_checksum_deterministic(temp_file):
    """Test that the checksum is deterministic for the same file."""
    checksum1 = calculate_checksum(temp_file)
    checksum2 = calculate_checksum(temp_file)
    assert checksum1 == checksum2

def test_calculate_checksum_different_content_different_hash():
    """Test that different file contents produce different hashes."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
        f1.write('content A')
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
        f2.write('content B')
        path2 = f2.name
    
    try:
        hash1 = calculate_checksum(path1)
        hash2 = calculate_checksum(path2)
        assert hash1 != hash2
    finally:
        os.unlink(path1)
        os.unlink(path2)

def test_calculate_checksum_file_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_checksum("/nonexistent/path/file.json")

def test_calculate_checksum_not_a_file():
    """Test that ValueError is raised for a directory path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            calculate_checksum(tmpdir)

def test_verify_checksum_matches(temp_file):
    """Test that verify_checksum returns True for correct checksum."""
    expected = calculate_checksum(temp_file)
    assert verify_checksum(temp_file, expected) is True

def test_verify_checksum_mismatch(temp_file):
    """Test that verify_checksum returns False for incorrect checksum."""
    wrong_checksum = "a" * 64
    assert verify_checksum(temp_file, wrong_checksum) is False

def test_verify_checksum_case_insensitive(temp_file):
    """Test that checksum verification is case-insensitive."""
    checksum = calculate_checksum(temp_file)
    assert verify_checksum(temp_file, checksum.upper()) is True
    assert verify_checksum(temp_file, checksum.lower()) is True

def test_verify_checksum_invalid_format():
    """Test that ValueError is raised for invalid checksum format."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write('test')
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            verify_checksum(temp_path, "invalid")
    finally:
        os.unlink(temp_path)

def test_generate_checksum_manifest(temp_file, temp_manifest):
    """Test that manifest is generated correctly."""
    generate_checksum_manifest([temp_file], temp_manifest)
    
    assert os.path.exists(temp_manifest)
    with open(temp_manifest, 'r') as f:
        manifest = json.load(f)
    
    assert Path(temp_file).name in manifest
    assert manifest[Path(temp_file).name] == calculate_checksum(temp_file)

def test_generate_checksum_manifest_multiple_files(temp_manifest):
    """Test manifest generation with multiple files."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f1:
        f1.write('file 1')
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f2:
        f2.write('file 2')
        path2 = f2.name
    
    try:
        generate_checksum_manifest([path1, path2], temp_manifest)
        
        with open(temp_manifest, 'r') as f:
            manifest = json.load(f)
        
        assert len(manifest) == 2
        assert Path(path1).name in manifest
        assert Path(path2).name in manifest
    finally:
        os.unlink(path1)
        os.unlink(path2)

def test_generate_checksum_manifest_skips_missing(temp_manifest):
    """Test that missing files are skipped without error."""
    generate_checksum_manifest(["/nonexistent/file.json"], temp_manifest)
    
    with open(temp_manifest, 'r') as f:
        manifest = json.load(f)
    
    assert len(manifest) == 0

def test_load_checksum_manifest(temp_file, temp_manifest):
    """Test loading a checksum manifest."""
    generate_checksum_manifest([temp_file], temp_manifest)
    
    manifest = load_checksum_manifest(temp_manifest)
    
    assert isinstance(manifest, dict)
    assert Path(temp_file).name in manifest
    assert manifest[Path(temp_file).name] == calculate_checksum(temp_file)

def test_load_checksum_manifest_not_found():
    """Test that FileNotFoundError is raised for missing manifest."""
    with pytest.raises(FileNotFoundError):
        load_checksum_manifest("/nonexistent/manifest.json")

def test_load_checksum_manifest_invalid_json(temp_manifest):
    """Test that JSONDecodeError is raised for invalid JSON."""
    with open(temp_manifest, 'w') as f:
        f.write("not valid json")
    
    with pytest.raises(json.JSONDecodeError):
        load_checksum_manifest(temp_manifest)
