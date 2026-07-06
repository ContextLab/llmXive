"""
Tests for data hygiene utilities.
"""
import os
import tempfile
import shutil
import hashlib
from pathlib import Path
import pytest
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.data_hygiene import (
    get_data_directories,
    scan_directory_for_files,
    compute_checksums_for_directory,
    record_directory_state,
    verify_data_integrity
)
from src.state_manager import save_state_file, load_state_file, calculate_file_hash


@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure with data directories."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create required directories
    (project_root / "data" / "raw").mkdir(parents=True)
    (project_root / "data" / "processed").mkdir(parents=True)
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_files(temp_project_structure):
    """Create sample files in data directories."""
    raw_dir = temp_project_structure / "data" / "raw"
    processed_dir = temp_project_structure / "data" / "processed"
    
    # Create sample files
    file1 = raw_dir / "test_file_1.txt"
    file1.write_text("content 1")
    
    file2 = raw_dir / "subdir" / "test_file_2.txt"
    file2.parent.mkdir(parents=True, exist_ok=True)
    file2.write_text("content 2")
    
    file3 = processed_dir / "processed_data.csv"
    file3.write_text("col1,col2\n1,2\n3,4")
    
    return {
        "raw": [file1, file2],
        "processed": [file3]
    }


def test_get_data_directories(temp_project_structure):
    dirs = get_data_directories(temp_project_structure)
    assert len(dirs) == 2
    assert (temp_project_structure / "data" / "raw") in dirs
    assert (temp_project_structure / "data" / "processed") in dirs


def test_scan_directory_for_files(sample_files):
    raw_files = scan_directory_for_files(sample_files["raw"][0].parent.parent)
    assert len(raw_files) == 2
    
    processed_files = scan_directory_for_files(sample_files["processed"][0].parent)
    assert len(processed_files) == 1


def test_compute_checksums_for_directory(sample_files):
    raw_checksums = compute_checksums_for_directory(sample_files["raw"][0].parent.parent)
    assert len(raw_checksums) == 2
    
    # Verify a specific hash
    file1 = sample_files["raw"][0]
    expected_hash = calculate_file_hash(file1)
    assert raw_checksums["test_file_1.txt"] == expected_hash


def test_record_directory_state(temp_project_structure, sample_files):
    state_file = temp_project_structure / "state.yaml"
    
    success = record_directory_state(temp_project_structure, state_file)
    assert success
    assert state_file.exists()
    
    state = load_state_file(state_file)
    assert "phases" in state
    assert len(state["phases"]) == 1
    assert "artifacts" in state["phases"][0]
    assert "raw" in state["phases"][0]["artifacts"]
    assert "processed" in state["phases"][0]["artifacts"]


def test_verify_data_integrity_valid(temp_project_structure, sample_files):
    state_file = temp_project_structure / "state.yaml"
    
    # Record initial state
    record_directory_state(temp_project_structure, state_file)
    
    # Verify
    is_valid, errors = verify_data_integrity(temp_project_structure, state_file)
    assert is_valid
    assert not errors


def test_verify_data_integrity_modified_file(temp_project_structure, sample_files):
    state_file = temp_project_structure / "state.yaml"
    
    # Record initial state
    record_directory_state(temp_project_structure, state_file)
    
    # Modify a file
    file1 = sample_files["raw"][0]
    file1.write_text("modified content")
    
    # Verify should fail
    is_valid, errors = verify_data_integrity(temp_project_structure, state_file)
    assert not is_valid
    assert "raw" in errors
    assert any("Modified file" in err for err in errors["raw"])


def test_verify_data_integrity_missing_file(temp_project_structure, sample_files):
    state_file = temp_project_structure / "state.yaml"
    
    # Record initial state
    record_directory_state(temp_project_structure, state_file)
    
    # Remove a file
    file1 = sample_files["raw"][0]
    file1.unlink()
    
    # Verify should fail
    is_valid, errors = verify_data_integrity(temp_project_structure, state_file)
    assert not is_valid
    assert "raw" in errors
    assert any("Missing file" in err for err in errors["raw"])


def test_verify_data_integrity_no_state_file(temp_project_structure):
    state_file = temp_project_structure / "nonexistent.yaml"
    is_valid, errors = verify_data_integrity(temp_project_structure, state_file)
    assert not is_valid
    assert "global" in errors
    assert any("not found" in err for err in errors["global"])
