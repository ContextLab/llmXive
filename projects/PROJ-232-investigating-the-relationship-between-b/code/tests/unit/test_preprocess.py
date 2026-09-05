import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import nibabel as nib

from src.data.preprocess import (
    ensure_directories,
    get_input_files,
    run_fmriprep_dry_run,
    validate_nifti_file,
    validate_preprocessed_outputs,
    FD_THRESHOLD
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_ensure_directories(temp_dir):
    ensure_directories(temp_dir)
    assert (temp_dir / "preprocessing").exists()
    assert (temp_dir / "preprocessing" / "fmriprep").exists()
    assert (temp_dir / "preprocessing" / "logs").exists()

def test_get_input_files_no_files(temp_dir):
    # Create a raw dir but no files
    (temp_dir / "data" / "raw").mkdir(parents=True)
    files = get_input_files(temp_dir)
    assert files == []

def test_run_fmriprep_dry_run(temp_dir):
    # Create a dummy input file
    input_dir = temp_dir / "data" / "raw"
    input_dir.mkdir(parents=True)
    input_file = input_dir / "sub-01_task-rest_bold.nii.gz"
    
    # Create a dummy 4D image
    data = np.random.rand(4, 4, 4, 10)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(input_file))
    
    output_dir = temp_dir / "data" / "preprocessing"
    output_dir.mkdir(parents=True)
    
    success = run_fmriprep_dry_run(input_file, output_dir)
    assert success is True
    
    # Check output exists
    fmriprep_dir = output_dir / "fmriprep"
    assert fmriprep_dir.exists()
    outputs = list(fmriprep_dir.glob("*_desc-preproc_bold.nii.gz"))
    assert len(outputs) == 1

def test_validate_nifti_file_valid(temp_dir):
    input_file = temp_dir / "valid.nii.gz"
    data = np.random.rand(4, 4, 4, 20)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(input_file))
    
    valid, msg = validate_nifti_file(input_file)
    assert valid is True
    assert "Valid" in msg

def test_validate_nifti_file_not_exists(temp_dir):
    input_file = temp_dir / "missing.nii.gz"
    valid, msg = validate_nifti_file(input_file)
    assert valid is False
    assert "does not exist" in msg

def test_validate_nifti_file_3d(temp_dir):
    input_file = temp_dir / "3d.nii.gz"
    data = np.random.rand(4, 4, 4)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(input_file))
    
    valid, msg = validate_nifti_file(input_file)
    assert valid is False
    assert "4D" in msg

def test_validate_nifti_file_all_zeros(temp_dir):
    input_file = temp_dir / "zeros.nii.gz"
    data = np.zeros((4, 4, 4, 10))
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(input_file))
    
    valid, msg = validate_nifti_file(input_file)
    assert valid is False
    assert "all zeros" in msg

def test_validate_preprocessed_outputs_pass(temp_dir):
    # Setup structure
    fmriprep_dir = temp_dir / "data" / "preprocessing" / "fmriprep"
    fmriprep_dir.mkdir(parents=True)
    
    # Create valid file
    input_file = fmriprep_dir / "sub-01_desc-preproc_bold.nii.gz"
    data = np.random.rand(4, 4, 4, 20)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, str(input_file))
    
    report = validate_preprocessed_outputs(temp_dir)
    assert report["status"] == "pass"
    assert report["valid_files"] == 1

def test_validate_preprocessed_outputs_fail_missing(temp_dir):
    # Setup empty directory
    fmriprep_dir = temp_dir / "data" / "preprocessing" / "fmriprep"
    fmriprep_dir.mkdir(parents=True)
    
    report = validate_preprocessed_outputs(temp_dir)
    assert report["status"] == "fail"
    assert "No NIfTI files" in report["reason"]