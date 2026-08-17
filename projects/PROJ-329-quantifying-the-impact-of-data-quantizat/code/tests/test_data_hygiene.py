"""
Tests for data hygiene utilities (checksumming, integrity verification).
"""
import os
import tempfile
import shutil
import hashlib
from pathlib import Path
import pytest
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_hygiene import (
    get_data_directories,
    scan_directory_for_files,
    compute_checksums_for_directory,
    record_directory_state,
    verify_data_integrity
)
from src.state_manager import calculate_file_hash, save_state_file

@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure mimicking the project layout."""
    tmp_dir = tempfile.mkdtemp()
    project_root = Path(tmp_dir)
    
    # Create data directories
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    data_results = project_root / "data" / "results"
    
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    data_results.mkdir(parents=True)
    
    # Create some sample files
    (data_raw / "noise_file.h5").write_text("fake noise data")
    (data_raw / "psd.csv").write_text("1,2,3")
    (data_processed / "waveform.h5").write_text("fake waveform data")
    (data_results / "metrics.json").write_text('{"mse": 0.01}')
    
    yield project_root
    
    shutil.rmtree(tmp_dir)

@pytest.fixture
def sample_files(temp_project_structure):
    """Return paths to sample files created in temp_project_structure."""
    root = temp_project_structure
    return {
        "raw_noise": root / "data" / "raw" / "noise_file.h5",
        "raw_psd": root / "data" / "raw" / "psd.csv",
        "processed_wf": root / "data" / "processed" / "waveform.h5",
        "results_metrics": root / "data" / "results" / "metrics.json"
    }

def test_get_data_directories(temp_project_structure):
    """Test that get_data_directories returns correct paths."""
    # Temporarily change __file__ context or mock
    # Since get_data_directories infers from __file__, we test the logic directly
    # by checking if the function returns expected relative structure
    dirs = get_data_directories()
    
    # The function infers from its own location, so we check keys exist
    assert "raw" in dirs
    assert "processed" in dirs
    assert "results" in dirs
    assert isinstance(dirs["raw"], Path)

def test_scan_directory_for_files(temp_project_structure, sample_files):
    """Test scanning directories for files."""
    raw_dir = temp_project_structure / "data" / "raw"
    
    # Scan all files
    files = scan_directory_for_files(raw_dir)
    assert len(files) == 2
    assert sample_files["raw_noise"] in files
    assert sample_files["raw_psd"] in files
    
    # Scan with extension filter
    files_h5 = scan_directory_for_files(raw_dir, extensions=[".h5"])
    assert len(files_h5) == 1
    assert files_h5[0] == sample_files["raw_noise"]
    
    # Scan non-existent directory
    with pytest.raises(FileNotFoundError):
        scan_directory_for_files(Path("/nonexistent"))

def test_compute_checksums_for_directory(temp_project_structure, sample_files):
    """Test computing checksums for a directory."""
    raw_dir = temp_project_structure / "data" / "raw"
    
    checksums = compute_checksums_for_directory(raw_dir)
    
    assert len(checksums) == 2
    
    # Verify checksums match calculated values
    noise_hash = calculate_file_hash(sample_files["raw_noise"])
    psd_hash = calculate_file_hash(sample_files["raw_psd"])
    
    assert checksums["noise_file.h5"] == noise_hash
    assert checksums["psd.csv"] == psd_hash

def test_record_directory_state(temp_project_structure, sample_files):
    """Test recording directory state to state.yaml."""
    raw_dir = temp_project_structure / "data" / "raw"
    state_file = temp_project_structure / "state.yaml"
    
    checksums = record_directory_state(raw_dir, state_file)
    
    assert len(checksums) == 2
    assert state_file.exists()
    
    # Verify state file content
    import yaml
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "data_checksums" in state
    assert "raw" in state["data_checksums"]
    assert state["data_checksums"]["raw"] == checksums

def test_verify_data_integrity_valid(temp_project_structure, sample_files):
    """Test verifying integrity when data is unchanged."""
    raw_dir = temp_project_structure / "data" / "raw"
    state_file = temp_project_structure / "state.yaml"
    
    # Record state first
    record_directory_state(raw_dir, state_file)
    
    # Verify immediately (should pass)
    is_valid, details = verify_data_integrity(raw_dir, state_file)
    
    assert is_valid is True
    assert len(details["missing"]) == 0
    assert len(details["modified"]) == 0
    assert len(details["unchanged"]) == 2

def test_verify_data_integrity_modified_file(temp_project_structure, sample_files):
    """Test verifying integrity when a file is modified."""
    raw_dir = temp_project_structure / "data" / "raw"
    state_file = temp_project_structure / "state.yaml"
    
    # Record state
    record_directory_state(raw_dir, state_file)
    
    # Modify a file
    (raw_dir / "psd.csv").write_text("modified content")
    
    # Verify (should fail)
    is_valid, details = verify_data_integrity(raw_dir, state_file)
    
    assert is_valid is False
    assert "psd.csv" in details["modified"]
    assert len(details["missing"]) == 0

def test_verify_data_integrity_missing_file(temp_project_structure, sample_files):
    """Test verifying integrity when a file is missing."""
    raw_dir = temp_project_structure / "data" / "raw"
    state_file = temp_project_structure / "state.yaml"
    
    # Record state
    record_directory_state(raw_dir, state_file)
    
    # Remove a file
    (raw_dir / "psd.csv").unlink()
    
    # Verify (should fail)
    is_valid, details = verify_data_integrity(raw_dir, state_file)
    
    assert is_valid is False
    assert "psd.csv" in details["missing"]
    assert len(details["modified"]) == 0

def test_verify_data_integrity_no_state_file(temp_project_structure):
    """Test verifying integrity when no state file exists."""
    raw_dir = temp_project_structure / "data" / "raw"
    state_file = temp_project_structure / "nonexistent_state.yaml"
    
    is_valid, details = verify_data_integrity(raw_dir, state_file)
    
    assert is_valid is False
    assert "error" in details
    assert "State file not found" in details["error"]
