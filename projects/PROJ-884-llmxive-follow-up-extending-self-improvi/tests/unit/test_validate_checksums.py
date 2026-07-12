import json
import os
import tempfile
from pathlib import Path
import pytest

from code.dataset.validate_checksums import (
    compute_file_checksum,
    generate_checksums_for_directory,
    validate_data_integrity,
    save_checksums,
    load_checksums
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary directory with some mock JSON files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create mock puzzle files
    file1 = data_dir / "puzzle_001.json"
    file1.write_text(json.dumps({"id": 1, "data": "test"}))
    
    file2 = data_dir / "puzzle_002.json"
    file2.write_text(json.dumps({"id": 2, "data": "test2"}))
    
    # Create a non-JSON file to ensure it's ignored
    (data_dir / "readme.txt").write_text("ignore me")
    
    return data_dir

def test_compute_file_checksum(temp_data_dir):
    file_path = temp_data_dir / "puzzle_001.json"
    checksum = compute_file_checksum(file_path)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)

    # Verify consistency
    checksum2 = compute_file_checksum(file_path)
    assert checksum == checksum2

def test_generate_checksums_for_directory(temp_data_dir):
    checksums = generate_checksums_for_directory(temp_data_dir)
    
    assert "puzzle_001.json" in checksums
    assert "puzzle_002.json" in checksums
    assert "readme.txt" not in checksums
    assert len(checksums) == 2

def test_save_and_load_checksums(temp_data_dir, tmp_path):
    checksums = generate_checksums_for_directory(temp_data_dir)
    output_path = tmp_path / "checksums.json"
    
    save_checksums(checksums, output_path)
    assert output_path.exists()
    
    loaded = load_checksums(output_path)
    assert loaded == checksums

def test_validate_data_integrity_pass(temp_data_dir, tmp_path):
    # Generate and save checksums
    checksums = generate_checksums_for_directory(temp_data_dir)
    checksum_file = tmp_path / "checksums.json"
    save_checksums(checksums, checksum_file)
    
    # Validate
    is_valid = validate_data_integrity(temp_data_dir, checksum_file)
    assert is_valid is True

def test_validate_data_integrity_fail_modification(temp_data_dir, tmp_path):
    # Generate and save checksums
    checksums = generate_checksums_for_directory(temp_data_dir)
    checksum_file = tmp_path / "checksums.json"
    save_checksums(checksums, checksum_file)
    
    # Modify a file
    file_path = temp_data_dir / "puzzle_001.json"
    file_path.write_text(json.dumps({"id": 1, "data": "MODIFIED"}))
    
    # Validate should fail
    is_valid = validate_data_integrity(temp_data_dir, checksum_file)
    assert is_valid is False

def test_validate_data_integrity_fail_missing_file(temp_data_dir, tmp_path):
    # Generate and save checksums
    checksums = generate_checksums_for_directory(temp_data_dir)
    checksum_file = tmp_path / "checksums.json"
    save_checksums(checksums, checksum_file)
    
    # Delete a file
    (temp_data_dir / "puzzle_001.json").unlink()
    
    # Validate should fail
    is_valid = validate_data_integrity(temp_data_dir, checksum_file)
    assert is_valid is False