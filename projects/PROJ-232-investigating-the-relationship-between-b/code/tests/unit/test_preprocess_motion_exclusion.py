import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Mock the logger to avoid noise in tests
import sys
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.data.preprocess import (
    exclude_high_motion_subjects, 
    calculate_framewise_displacement, 
    ensure_directories,
    get_input_files,
    DEFAULT_FD_THRESHOLD
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking data/preprocessing/sub-*/func/"""
    data_dir = tmp_path / "data" / "preprocessing"
    data_dir.mkdir(parents=True)
    
    # Create subjects
    subjects = {
        "sub-01": 0.2,  # Low motion
        "sub-02": 0.6,  # High motion (> 0.5)
        "sub-03": 0.4,  # Low motion
        "sub-04": 1.2,  # High motion
    }
    
    files_created = []
    for sub_id, fd_val in subjects.items():
        sub_dir = data_dir / sub_id / "func"
        sub_dir.mkdir(parents=True)
        
        # Create dummy NIfTI (we won't actually read it, just check path)
        nifti_path = sub_dir / f"{sub_id}_task-rest_space-MNI_desc-preproc_bold.nii.gz"
        nifti_path.touch()
        
        # Create dummy confounds.tsv with FD column
        confounds_path = sub_dir / "confounds.tsv"
        with open(confounds_path, 'w') as f:
            # Write header
            f.write("framewise_displacement\n")
            # Write mean FD for 100 volumes
            for _ in range(100):
                f.write(f"{fd_val}\n")
        
        files_created.append(nifti_path)
    
    return tmp_path, data_dir, subjects

def test_calculate_framewise_displacement(temp_data_dir):
    tmp_path, data_dir, subjects = temp_data_dir
    nifti_path = data_dir / "sub-01" / "func" / "sub-01_task-rest_space-MNI_desc-preproc_bold.nii.gz"
    
    fd = calculate_framewise_displacement(nifti_path)
    assert abs(fd - 0.2) < 1e-6, f"Expected FD 0.2, got {fd}"

def test_exclude_high_motion_subjects(temp_data_dir):
    tmp_path, data_dir, subjects = temp_data_dir
    log_path = tmp_path / "data" / "preprocessing" / "run_log.json"
    
    result = exclude_high_motion_subjects(data_dir, threshold=0.5, run_log_path=log_path)
    
    # Check included
    assert "sub-01" in result["included_subjects"]
    assert "sub-03" in result["included_subjects"]
    
    # Check excluded
    assert "sub-02" in result["excluded_subjects"]
    assert "sub-04" in result["excluded_subjects"]
    
    # Check log file exists and has content
    assert log_path.exists()
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert "excluded_subjects" in log_data
    assert "sub-02" in log_data["excluded_subjects"]
    assert "sub-04" in log_data["excluded_subjects"]
    assert "fd_metrics" in log_data
    assert abs(log_data["fd_metrics"]["sub-01"] - 0.2) < 1e-6
    assert abs(log_data["fd_metrics"]["sub-02"] - 0.6) < 1e-6

def test_exclude_high_motion_subjects_no_files(tmp_path):
    data_dir = tmp_path / "data" / "preprocessing"
    data_dir.mkdir(parents=True)
    
    log_path = tmp_path / "data" / "preprocessing" / "run_log.json"
    
    result = exclude_high_motion_subjects(data_dir, threshold=0.5, run_log_path=log_path)
    
    assert result["status"] == "no_data"
    assert len(result["included_subjects"]) == 0
    assert len(result["excluded_subjects"]) == 0

def test_exclude_high_motion_subjects_all_high(tmp_path):
    data_dir = tmp_path / "data" / "preprocessing"
    data_dir.mkdir(parents=True)
    
    # Create one high motion subject
    sub_dir = data_dir / "sub-99" / "func"
    sub_dir.mkdir(parents=True)
    nifti_path = sub_dir / "sub-99_task-rest_space-MNI_desc-preproc_bold.nii.gz"
    nifti_path.touch()
    
    confounds_path = sub_dir / "confounds.tsv"
    with open(confounds_path, 'w') as f:
        f.write("framewise_displacement\n")
        for _ in range(100):
            f.write("0.8\n") # High FD
    
    log_path = tmp_path / "data" / "preprocessing" / "run_log.json"
    result = exclude_high_motion_subjects(data_dir, threshold=0.5, run_log_path=log_path)
    
    assert "sub-99" in result["excluded_subjects"]
    assert len(result["included_subjects"]) == 0