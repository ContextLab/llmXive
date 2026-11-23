"""
Unit tests for data hygiene utilities (checksumming and integrity verification).
"""
import os
import tempfile
import shutil
import hashlib
from pathlib import Path
import pytest

import sys
# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_hygiene import (
    get_data_directories,
    scan_directory_for_files,
    compute_checksums_for_directory,
    verify_data_integrity,
    record_directory_state
)
from src.state_manager import save_state_file, load_state_file


@pytest.fixture
def temp_project_structure():
    """Creates a temporary directory structure mimicking the project data folders."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir) / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    
    # Create sample files
    (raw_dir / "noise.h5").write_text("fake noise data")
    (raw_dir / "config.json").write_text('{"seed": 42}')
    (processed_dir / "waveforms.h5").write_text("fake waveform data")
    
    yield {
        "root": Path(temp_dir),
        "raw": raw_dir,
        "processed": processed_dir,
        "data": data_dir
    }
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_files(temp_project_structure):
    """Returns the paths of sample files created in the fixture."""
    return {
        "raw_noise": temp_project_structure["raw"] / "noise.h5",
        "raw_config": temp_project_structure["raw"] / "config.json",
        "processed_wf": temp_project_structure["processed"] / "waveforms.h5"
    }


def test_get_data_directories(temp_project_structure):
    """Test that get_data_directories finds the created directories."""
    # Temporarily override the global constants in data_hygiene
    import src.data_hygiene as dh
    original_root = dh.PROJECT_ROOT
    
    # Mock the project root to our temp structure
    # We need to patch the module's internal variables
    dh.PROJECT_ROOT = temp_project_structure["root"]
    dh.DATA_RAW_DIR = temp_project_structure["raw"]
    dh.DATA_PROCESSED_DIR = temp_project_structure["processed"]
    dh.DATA_RESULTS_DIR = temp_project_structure["root"] / "data" / "results" # Doesn't exist
    
    try:
        dirs = get_data_directories()
        assert len(dirs) == 2
        assert temp_project_structure["raw"] in dirs
        assert temp_project_structure["processed"] in dirs
    finally:
        # Restore original
        dh.PROJECT_ROOT = original_root
        dh.DATA_RAW_DIR = Path(original_root) / "data" / "raw"
        dh.DATA_PROCESSED_DIR = Path(original_root) / "data" / "processed"
        dh.DATA_RESULTS_DIR = Path(original_root) / "data" / "results"


def test_scan_directory_for_files(temp_project_structure):
    """Test recursive file scanning."""
    files = scan_directory_for_files(temp_project_structure["raw"])
    assert len(files) == 2
    assert temp_project_structure["raw"] / "noise.h5" in files
    
    # Test extension filter
    files_json = scan_directory_for_files(temp_project_structure["raw"], extensions=[".json"])
    assert len(files_json) == 1
    assert temp_project_structure["raw"] / "config.json" in files_json


def test_compute_checksums_for_directory(temp_project_structure):
    """Test checksum calculation."""
    checksums = compute_checksums_for_directory(temp_project_structure["raw"])
    assert len(checksums) == 2
    
    # Verify specific hash for a known string
    expected_hash = hashlib.sha256(b"fake noise data").hexdigest()
    assert checksums["noise.h5"] == expected_hash


def test_record_directory_state(temp_project_structure):
    """Test recording directory state to a YAML file."""
    state_file = temp_project_structure["root"] / "state.yaml"
    
    success = record_directory_state(temp_project_structure["raw"], state_file=state_file)
    assert success
    assert state_file.exists()
    
    state_data = load_state_file(state_file)
    assert "data_checksums" in state_data
    assert "raw" in state_data["data_checksums"]
    assert "noise.h5" in state_data["data_checksums"]["raw"]


def test_verify_data_integrity_valid(temp_project_structure):
    """Test verification when data matches state."""
    state_file = temp_project_structure["root"] / "state.yaml"
    
    # Record state
    record_directory_state(temp_project_structure["raw"], state_file=state_file)
    
    # Verify immediately (should be valid)
    is_valid, current, expected = verify_data_integrity(temp_project_structure["raw"], state_file=state_file)
    assert is_valid
    assert current == expected


def test_verify_data_integrity_modified_file(temp_project_structure):
    """Test verification fails when a file is modified."""
    state_file = temp_project_structure["root"] / "state.yaml"
    
    # Record state
    record_directory_state(temp_project_structure["raw"], state_file=state_file)
    
    # Modify a file
    (temp_project_structure["raw"] / "noise.h5").write_text("modified data")
    
    # Verify (should be invalid)
    is_valid, current, expected = verify_data_integrity(temp_project_structure["raw"], state_file=state_file)
    assert not is_valid
    assert current["noise.h5"] != expected["noise.h5"]


def test_verify_data_integrity_missing_file(temp_project_structure):
    """Test verification fails when a file is deleted."""
    state_file = temp_project_structure["root"] / "state.yaml"
    
    # Record state
    record_directory_state(temp_project_structure["raw"], state_file=state_file)
    
    # Delete a file
    (temp_project_structure["raw"] / "config.json").unlink()
    
    # Verify (should be invalid)
    is_valid, current, expected = verify_data_integrity(temp_project_structure["raw"], state_file=state_file)
    assert not is_valid
    assert "config.json" not in current
    assert "config.json" in expected


def test_verify_data_integrity_no_state_file(temp_project_structure):
    """Test verification fails gracefully if state file is missing."""
    fake_state = temp_project_structure["root"] / "nonexistent.yaml"
    
    is_valid, current, expected = verify_data_integrity(temp_project_structure["raw"], state_file=fake_state)
    assert not is_valid
    assert expected == {}
    assert current == {}
