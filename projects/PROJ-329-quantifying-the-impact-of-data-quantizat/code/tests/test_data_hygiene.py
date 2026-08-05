"""
Tests for data_hygiene module.
"""
import os
import tempfile
import shutil
import hashlib
from pathlib import Path
import pytest

import sys
# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_hygiene import (
    get_data_directories,
    scan_directory_for_files,
    compute_checksums_for_directory,
    verify_data_integrity,
    record_directory_state
)
from src.state_manager import save_state_file


@pytest.fixture
def temp_project_structure():
    """Creates a temporary directory structure mimicking the project layout."""
    temp_dir = tempfile.mkdtemp()
    # Create structure
    data_raw = Path(temp_dir) / "data" / "raw"
    data_processed = Path(temp_dir) / "data" / "processed"
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    
    # Create some dummy files
    (data_raw / "file1.txt").write_text("content1")
    (data_raw / "file2.bin").write_bytes(b"\x00\x01\x02")
    (data_processed / "result.csv").write_text("a,b,c\n1,2,3")
    
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_files(temp_project_structure):
    """Returns paths to the sample files created in the fixture."""
    return {
        "raw": [
            Path(temp_project_structure) / "data" / "raw" / "file1.txt",
            Path(temp_project_structure) / "data" / "raw" / "file2.bin"
        ],
        "processed": [
            Path(temp_project_structure) / "data" / "processed" / "result.csv"
        ]
    }


def test_get_data_directories(temp_project_structure):
    """Test that get_data_directories returns correct paths."""
    raw, processed = get_data_directories(Path(temp_project_structure))
    assert raw == Path(temp_project_structure) / "data" / "raw"
    assert processed == Path(temp_project_structure) / "data" / "processed"
    assert raw.exists()
    assert processed.exists()


def test_scan_directory_for_files(temp_project_structure):
    """Test scanning a directory for files."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    files = scan_directory_for_files(raw_dir)
    
    assert len(files) == 2
    file_names = [f.name for f in files]
    assert "file1.txt" in file_names
    assert "file2.bin" in file_names


def test_compute_checksums_for_directory(temp_project_structure):
    """Test computing checksums for a directory."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    checksums = compute_checksums_for_directory(raw_dir)
    
    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "file2.bin" in checksums
    
    # Verify one hash manually
    content = (raw_dir / "file1.txt").read_text()
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    assert checksums["file1.txt"] == expected_hash


def test_record_directory_state(temp_project_structure):
    """Test recording directory state to a file."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    processed_dir = Path(temp_project_structure) / "data" / "processed"
    
    raw_checksums = compute_checksums_for_directory(raw_dir)
    processed_checksums = compute_checksums_for_directory(processed_dir)
    
    state_file = Path(temp_project_structure) / "state.yaml"
    
    success = record_directory_state(raw_checksums, processed_checksums, state_file)
    assert success
    assert state_file.exists()
    
    # Verify content
    from src.state_manager import load_state_file
    state = load_state_file(state_file)
    assert "data_raw" in state
    assert "data_processed" in state
    assert len(state["data_raw"]) == 2
    assert len(state["data_processed"]) == 1


def test_verify_data_integrity_valid(temp_project_structure):
    """Test verification when data has not changed."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    processed_dir = Path(temp_project_structure) / "data" / "processed"
    
    raw_checksums = compute_checksums_for_directory(raw_dir)
    processed_checksums = compute_checksums_for_directory(processed_dir)
    
    state_file = Path(temp_project_structure) / "state.yaml"
    record_directory_state(raw_checksums, processed_checksums, state_file)
    
    # Re-compute and verify
    new_raw = compute_checksums_for_directory(raw_dir)
    new_processed = compute_checksums_for_directory(processed_dir)
    
    is_valid, errors = verify_data_integrity(new_raw, new_processed, state_file)
    assert is_valid
    assert len(errors) == 0


def test_verify_data_integrity_modified_file(temp_project_structure):
    """Test verification when a file content has changed."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    processed_dir = Path(temp_project_structure) / "data" / "processed"
    
    # Initial state
    raw_checksums = compute_checksums_for_directory(raw_dir)
    processed_checksums = compute_checksums_for_directory(processed_dir)
    state_file = Path(temp_project_structure) / "state.yaml"
    record_directory_state(raw_checksums, processed_checksums, state_file)
    
    # Modify a file
    (raw_dir / "file1.txt").write_text("modified content")
    
    # Verify should fail
    new_raw = compute_checksums_for_directory(raw_dir)
    is_valid, errors = verify_data_integrity(new_raw, processed_checksums, state_file)
    
    assert not is_valid
    assert any("file1.txt" in err for err in errors)


def test_verify_data_integrity_missing_file(temp_project_structure):
    """Test verification when a file is missing."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    processed_dir = Path(temp_project_structure) / "data" / "processed"
    
    # Initial state
    raw_checksums = compute_checksums_for_directory(raw_dir)
    processed_checksums = compute_checksums_for_directory(processed_dir)
    state_file = Path(temp_project_structure) / "state.yaml"
    record_directory_state(raw_checksums, processed_checksums, state_file)
    
    # Remove a file
    (raw_dir / "file1.txt").unlink()
    
    # Verify should fail
    new_raw = compute_checksums_for_directory(raw_dir)
    is_valid, errors = verify_data_integrity(new_raw, processed_checksums, state_file)
    
    assert not is_valid
    assert any("missing" in err for err in errors)


def test_verify_data_integrity_no_state_file(temp_project_structure):
    """Test verification when no state file exists."""
    raw_dir = Path(temp_project_structure) / "data" / "raw"
    processed_dir = Path(temp_project_structure) / "data" / "processed"
    
    raw_checksums = compute_checksums_for_directory(raw_dir)
    processed_checksums = compute_checksums_for_directory(processed_dir)
    
    fake_state_path = Path(temp_project_structure) / "non_existent.yaml"
    
    is_valid, errors = verify_data_integrity(raw_checksums, processed_checksums, fake_state_path)
    
    assert not is_valid
    assert len(errors) > 0
    assert "not found" in errors[0].lower()
