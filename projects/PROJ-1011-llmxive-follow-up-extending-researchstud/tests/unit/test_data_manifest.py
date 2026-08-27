import os
import json
import tempfile
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.data_manifest import (
    create_directory_structure,
    calculate_file_checksum,
    load_manifest,
    save_manifest,
    update_manifest_with_file,
    verify_manifest,
    register_new_file,
    MANIFEST_FILENAME
)
from utils.error_handling import ValidationError

@pytest.fixture
def temp_data_root():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_create_directory_structure(temp_data_root):
    """Test that create_directory_structure creates the required subdirectories."""
    result = create_directory_structure(temp_data_root)
    
    assert result.exists()
    assert (result / "raw").exists()
    assert (result / "processed").exists()
    assert (result / "results").exists()
    assert (result / MANIFEST_FILENAME).exists()

def test_create_directory_structure_idempotent(temp_data_root):
    """Test that calling create_directory_structure twice doesn't fail."""
    create_directory_structure(temp_data_root)
    # Should not raise
    create_directory_structure(temp_data_root)
    
    assert (temp_data_root / "raw").exists()
    assert (temp_data_root / "processed").exists()
    assert (temp_data_root / "results").exists()

def test_calculate_file_checksum(temp_data_root):
    """Test checksum calculation."""
    test_file = temp_data_root / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    checksum = calculate_file_checksum(test_file)
    
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length
    
    # Verify consistency
    assert calculate_file_checksum(test_file) == checksum

def test_calculate_file_checksum_missing_file(temp_data_root):
    """Test that calculating checksum for missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(temp_data_root / "nonexistent.txt")

def test_load_manifest_missing(temp_data_root):
    """Test that loading manifest from non-initialized directory raises error."""
    # Don't run create_directory_structure, so manifest doesn't exist
    with pytest.raises(ValidationError):
        load_manifest(temp_data_root)

def test_load_manifest_success(temp_data_root):
    """Test loading an existing manifest."""
    create_directory_structure(temp_data_root)
    
    manifest = load_manifest(temp_data_root)
    assert isinstance(manifest, dict)

def test_update_manifest_with_file(temp_data_root):
    """Test updating manifest with a new file."""
    create_directory_structure(temp_data_root)
    
    test_file = temp_data_root / "raw" / "sample.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Sample content")
    
    update_manifest_with_file(temp_data_root, test_file)
    
    manifest = load_manifest(temp_data_root)
    assert str(test_file.relative_to(temp_data_root)) in manifest
    
    entry = manifest[str(test_file.relative_to(temp_data_root))]
    assert "checksum" in entry
    assert "size_bytes" in entry
    assert "path" in entry

def test_verify_manifest_valid(temp_data_root):
    """Test verifying a manifest with valid files."""
    create_directory_structure(temp_data_root)
    
    test_file = temp_data_root / "raw" / "valid.txt"
    test_file.write_text("Valid content")
    
    update_manifest_with_file(temp_data_root, test_file)
    
    assert verify_manifest(temp_data_root) is True

def test_verify_manifest_corrupted(temp_data_root):
    """Test verifying a manifest with corrupted file content."""
    create_directory_structure(temp_data_root)
    
    test_file = temp_data_root / "raw" / "corrupted.txt"
    test_file.write_text("Original content")
    
    update_manifest_with_file(temp_data_root, test_file)
    
    # Corrupt the file
    test_file.write_text("Corrupted content")
    
    assert verify_manifest(temp_data_root) is False

def test_register_new_file(temp_data_root):
    """Test registering a new file."""
    create_directory_structure(temp_data_root)
    
    test_file = temp_data_root / "processed" / "data.json"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text('{"key": "value"}')
    
    checksum = register_new_file(temp_data_root, test_file, {"type": "json"})
    
    manifest = load_manifest(temp_data_root)
    entry = manifest[str(test_file.relative_to(temp_data_root))]
    
    assert entry["checksum"] == checksum
    assert entry["type"] == "json"
    assert entry["size_bytes"] > 0
