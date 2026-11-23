"""
Unit tests for T015: save_processed_data module.

Tests verify that:
1. Time series are saved correctly
2. Metadata is saved correctly
3. Checksums are computed and updated in state file
4. File paths are correct
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pytest
import nibabel as nib
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.save_processed_data import (
    save_time_series_nifti,
    save_metadata,
    update_state_checksums,
    compute_file_sha256
)
from code.utils.checksum import compute_file_sha256 as utils_compute_sha256

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_base = tempfile.mkdtemp()
    output_dir = Path(temp_base) / "processed"
    output_dir.mkdir()
    yield output_dir
    shutil.rmtree(temp_base)

@pytest.fixture
def sample_time_series():
    """Generate sample time series data."""
    num_timepoints = 120
    num_regions = 100
    return np.random.randn(num_timepoints, num_regions).astype(np.float32)

@pytest.fixture
def sample_metadata():
    """Generate sample metadata."""
    return {
        "subject_id": "test_sub_001",
        "fluid_intelligence": 105.5,
        "mean_fd": 0.15,
        "preprocessing_params": {
            "low_freq": 0.01,
            "high_freq": 0.1
        }
    }

@pytest.fixture
def sample_nifti(temp_dirs):
    """Create a sample NIfTI file for reference."""
    data = np.random.randn(10, 10, 10, 120).astype(np.float32)
    img = nib.Nifti1Image(data, np.eye(4))
    path = temp_dirs / "reference.nii.gz"
    nib.save(img, str(path))
    return path

def test_save_time_series_nifti(temp_dirs, sample_time_series, sample_nifti):
    """Test saving time series as NIfTI."""
    subject_id = "test_sub_001"
    output_path = save_time_series_nifti(
        subject_id, 
        sample_time_series, 
        sample_nifti, 
        temp_dirs
    )
    
    assert output_path.exists()
    assert output_path.name == f"{subject_id}_timeseries.nii.gz"
    
    # Load and verify
    loaded_img = nib.load(str(output_path))
    loaded_data = loaded_img.get_fdata()
    
    # Shape should be (1, 1, regions, timepoints)
    assert loaded_data.shape[2] == sample_time_series.shape[1]
    assert loaded_data.shape[3] == sample_time_series.shape[0]

def test_save_metadata(temp_dirs, sample_metadata):
    """Test saving metadata as JSON."""
    subject_id = "test_sub_001"
    output_path = save_metadata(subject_id, sample_metadata, temp_dirs)
    
    assert output_path.exists()
    assert output_path.name == f"{subject_id}_metadata.json"
    
    # Load and verify
    with open(output_path, 'r') as f:
        loaded_meta = json.load(f)
    
    assert loaded_meta["subject_id"] == sample_metadata["subject_id"]
    assert loaded_meta["fluid_intelligence"] == sample_metadata["fluid_intelligence"]

def test_compute_file_sha256(temp_dirs):
    """Test SHA-256 checksum computation."""
    test_file = temp_dirs / "test.txt"
    test_content = "test content for checksum"
    test_file.write_text(test_content)
    
    checksum = compute_file_sha256(test_file)
    
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_update_state_checksums(temp_dirs):
    """Test updating state file with checksums."""
    state_path = Path(temp_dirs) / "test_state.yaml"
    checksums = {
        "data/processed/test.nii.gz": "abc123...",
        "data/processed/test_meta.json": "def456..."
    }
    
    update_state_checksums(checksums, state_path)
    
    assert state_path.exists()
    
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "artifact_hashes" in state
    assert state["artifact_hashes"]["data/processed/test.nii.gz"] == "abc123..."
    assert state["artifact_hashes"]["data/processed/test_meta.json"] == "def456..."
    assert state["project_id"] == "PROJ-190-investigating-the-relationship-between-b"

def test_update_state_checksums_existing(temp_dirs):
    """Test updating an existing state file."""
    state_path = Path(temp_dirs) / "existing_state.yaml"
    
    # Create initial state
    initial_state = {
        "project_id": "PROJ-190-test",
        "artifact_hashes": {
            "existing/file.nii.gz": "old_checksum"
        }
    }
    with open(state_path, 'w') as f:
        yaml.dump(initial_state, f)
    
    # Update with new checksums
    new_checksums = {
        "new/file.nii.gz": "new_checksum"
    }
    update_state_checksums(new_checksums, state_path)
    
    with open(state_path, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "existing/file.nii.gz" in state["artifact_hashes"]
    assert "new/file.nii.gz" in state["artifact_hashes"]
    assert state["artifact_hashes"]["existing/file.nii.gz"] == "old_checksum"
    assert state["artifact_hashes"]["new/file.nii.gz"] == "new_checksum"
