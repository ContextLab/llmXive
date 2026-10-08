import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import nibabel as nib

from src.data.preprocess import (
    validate_nifti_file,
    validate_preprocessed_outputs,
    ensure_directories,
    get_input_files,
)
from src.config.env_config import get_data_path


@pytest.fixture
def temp_nifti_file():
    """Create a temporary valid 4D NIfTI file."""
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
        # Create a small 4D image: 10x10x10x20
        data = np.random.rand(10, 10, 10, 20) * 1000 + 1000
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, f.name)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_invalid_nifti_file():
    """Create a temporary invalid 4D NIfTI file (all zeros)."""
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
        data = np.zeros((10, 10, 10, 20))
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, f.name)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_3d_nifti_file():
    """Create a temporary 3D NIfTI file (invalid for fMRI)."""
    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as f:
        data = np.random.rand(10, 10, 10) * 1000 + 1000
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, f.name)
        yield f.name
    os.unlink(f.name)


def test_validate_nifti_file_valid(temp_nifti_file):
    """Test validation of a valid 4D NIfTI file."""
    result = validate_nifti_file(Path(temp_nifti_file))
    
    assert result["exists"] is True
    assert result["valid"] is True
    assert result["error"] is None
    assert result["metadata"]["shape"] == [10, 10, 10, 20]
    assert result["metadata"]["timepoints"] == 20


def test_validate_nifti_file_not_exists():
    """Test validation of a non-existent file."""
    result = validate_nifti_file(Path("/nonexistent/path/file.nii.gz"))
    
    assert result["exists"] is False
    assert result["valid"] is False
    assert "does not exist" in result["error"]


def test_validate_nifti_file_3d(temp_3d_nifti_file):
    """Test validation rejects 3D files."""
    result = validate_nifti_file(Path(temp_3d_nifti_file))
    
    assert result["valid"] is False
    assert "4D" in result["error"]


def test_validate_nifti_file_all_zeros(temp_invalid_nifti_file):
    """Test validation rejects all-zero images."""
    result = validate_nifti_file(Path(temp_invalid_nifti_file))
    
    assert result["valid"] is False
    assert "all zeros" in result["error"]


def test_validate_preprocessed_outputs_pass(tmp_path):
    """Test successful validation when preprocessed file exists."""
    # Setup: Create a fake preprocessed file
    fmriprep_dir = tmp_path / "fmriprep"
    fmriprep_dir.mkdir()
    
    subj_id = "001"
    fname = f"sub-{subj_id}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    fpath = fmriprep_dir / fname
    
    # Create a valid 4D NIfTI
    data = np.random.rand(10, 10, 10, 20) * 1000 + 1000
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(fpath))
    
    # Run validation
    result = validate_preprocessed_outputs(subj_id, tmp_path)
    
    assert result["validation_passed"] is True
    assert len(result["errors"]) == 0
    assert subj_id in result.get("files_checked", [])[0] if result.get("files_checked") else True


def test_validate_preprocessed_outputs_fail_missing(tmp_path):
    """Test validation fails when no preprocessed file exists."""
    result = validate_preprocessed_outputs("999", tmp_path)
    
    assert result["validation_passed"] is False
    assert len(result["errors"]) > 0
    assert "No preprocessed NIfTI file found" in result["errors"][0]


def test_validate_preprocessed_outputs_fail_invalid(tmp_path):
    """Test validation fails when preprocessed file is invalid (all zeros)."""
    fmriprep_dir = tmp_path / "fmriprep"
    fmriprep_dir.mkdir()
    
    subj_id = "002"
    fname = f"sub-{subj_id}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    fpath = fmriprep_dir / fname
    
    # Create an invalid 4D NIfTI (all zeros)
    data = np.zeros((10, 10, 10, 20))
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(fpath))
    
    # Run validation
    result = validate_preprocessed_outputs(subj_id, tmp_path)
    
    assert result["validation_passed"] is False
    assert len(result["errors"]) > 0
    assert "all zeros" in result["errors"][0]