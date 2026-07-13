"""
Integration test for motion correction module.
Verifies that motion correction runs on real data structure and produces expected outputs.
"""
import os
import tempfile
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path
import json

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from preprocessing.motion_correction import calculate_framewise_displacement, correct_motion
from utils.io import load_json, file_exists

def create_dummy_nifti_with_motion_params(tmp_path, n_volumes=100, seed=42):
    """
    Create a dummy 4D NIfTI file and a corresponding JSON sidecar with motion parameters.
    """
    np.random.seed(seed)
    
    # Create dummy 4D data
    shape = (10, 10, 10, n_volumes)
    data = np.random.randn(*shape)
    
    # Create affine
    affine = np.eye(4)
    
    # Create NIfTI image
    img = nib.Nifti1Image(data, affine)
    nii_path = tmp_path / 'sub-01_task-rest_bold.nii.gz'
    nib.save(img, str(nii_path))
    
    # Create dummy motion parameters (translations in mm, rotations in rad)
    # Simulate some motion
    trans = np.cumsum(np.random.randn(n_volumes, 3) * 0.5, axis=0)
    rot = np.cumsum(np.random.randn(n_volumes, 3) * 0.01, axis=0)
    
    # Combine into 6-column array
    motion_params = np.hstack([trans, rot])
    
    # Create JSON sidecar
    json_path = tmp_path / 'sub-01_task-rest_bold.json'
    json_data = {
        "RepetitionTime": 2.0,
        "MotionParameters": motion_params.tolist()
    }
    with open(json_path, 'w') as f:
        json.dump(json_data, f)
        
    return nii_path, json_path

def test_calculate_framewise_displacement():
    """Test FD calculation with known inputs."""
    # Zero motion should yield zero FD (except first frame)
    trans = np.zeros((10, 3))
    rot = np.zeros((10, 3))
    fd = calculate_framewise_displacement(trans, rot)
    assert len(fd) == 10
    assert np.allclose(fd[1:], 0.0)
    
    # Non-zero motion
    trans = np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0]]) # 1mm translation
    rot = np.zeros((3, 3))
    fd = calculate_framewise_displacement(trans, rot)
    # FD should be 1.0 for the second frame (1mm translation)
    assert np.isclose(fd[1], 1.0)

def test_correct_motion_integration(tmp_path):
    """Test the full motion correction pipeline on dummy data."""
    # Setup
    nii_path, json_path = create_dummy_nifti_with_motion_params(tmp_path)
    output_dir = tmp_path / 'output'
    
    # Run
    result = correct_motion(nii_path, output_dir, threshold=0.5)
    
    # Assertions
    assert 'fd_values' in result
    assert 'high_motion_indices' in result
    assert 'exclusion_reason' in result
    assert 'report_path' in result
    assert 'fd_csv_path' in result
    
    # Check files were created
    assert file_exists(result['report_path'])
    assert file_exists(result['fd_csv_path'])
    
    # Check report content
    report = load_json(result['report_path'])
    assert 'fd_stats' in report
    assert 'total_volumes' in report
    assert report['total_volumes'] == 100
    
    # Check CSV content
    import pandas as pd
    df = pd.read_csv(result['fd_csv_path'])
    assert 'volume' in df.columns
    assert 'fd' in df.columns
    assert len(df) == 100

def test_motion_correction_exclusion(tmp_path):
    """Test that high motion leads to exclusion."""
    # Create data with high motion
    np.random.seed(999)
    n_volumes = 100
    shape = (10, 10, 10, n_volumes)
    data = np.random.randn(*shape)
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    
    nii_path = tmp_path / 'sub-02_task-rest_bold.nii.gz'
    nib.save(img, str(nii_path))
    
    # Create high motion parameters (frequent large jumps)
    # Ensure >10% of volumes have FD > 3mm
    trans = np.random.randn(n_volumes, 3) * 5.0 # Large translations
    rot = np.random.randn(n_volumes, 3) * 0.1
    motion_params = np.hstack([trans, rot])
    
    json_path = tmp_path / 'sub-02_task-rest_bold.json'
    with open(json_path, 'w') as f:
        json.dump({"MotionParameters": motion_params.tolist()}, f)
    
    output_dir = tmp_path / 'output'
    result = correct_motion(nii_path, output_dir, threshold=3.0)
    
    # Check exclusion
    assert result['exclusion_reason'] is not None
    assert 'High motion' in result['exclusion_reason']
    assert result['exclusion_reason'].count('%') > 0 # Contains percentage

if __name__ == '__main__':
    pytest.main([__file__, '-v'])