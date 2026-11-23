import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from code.utils.motion import (
    calculate_mean_fd,
    check_motion_exclusion,
    generate_exclusion_log,
    process_subject_motion,
    run_motion_filtering_pipeline
)
from code.utils.logging import get_exclusion_log_path

def test_calculate_mean_fd():
    """Test Mean FD calculation with known motion parameters."""
    # Create synthetic motion parameters
    # 10 timepoints, 6 parameters
    motion_params = np.zeros((10, 6))
    
    # Add a known displacement in translation (x)
    # Diff will be 0.1mm for 9 frames
    motion_params[1:, 0] = 0.1 * np.arange(1, 10)
    
    # Rotations are 0, so only translation contributes
    mean_fd = calculate_mean_fd(motion_params)
    
    # Expected: sum of diffs / (n-1)
    # diffs: [0.1, 0.1, ..., 0.1] (9 times)
    # sum = 0.9
    # mean = 0.9 / 9 = 0.1
    assert np.isclose(mean_fd, 0.1, atol=1e-6), f"Expected 0.1, got {mean_fd}"

def test_check_motion_exclusion():
    """Test motion exclusion logic."""
    # Should not exclude
    assert not check_motion_exclusion(0.1, threshold=0.2)
    assert not check_motion_exclusion(0.2, threshold=0.2) # Exactly at threshold is OK
    
    # Should exclude
    assert check_motion_exclusion(0.2001, threshold=0.2)
    assert check_motion_exclusion(0.5, threshold=0.2)

def test_generate_exclusion_log(tmp_path):
    """Test that exclusion log is written correctly."""
    log_file = os.path.join(tmp_path, "test_exclusion_log.csv")
    
    # First call (creates file)
    generate_exclusion_log("SUBJ001", 0.25, "Motion", log_path=log_file)
    
    assert os.path.exists(log_file)
    df = pd.read_csv(log_file)
    assert len(df) == 1
    assert df.iloc[0]['Subject_ID'] == 'SUBJ001'
    assert df.iloc[0]['Exclusion_Reason'] == 'Motion'
    assert np.isclose(df.iloc[0]['Mean_FD'], 0.25)
    
    # Second call (appends)
    generate_exclusion_log("SUBJ002", 0.30, "Motion", log_path=log_file)
    df = pd.read_csv(log_file)
    assert len(df) == 2
    assert df.iloc[1]['Subject_ID'] == 'SUBJ002'

def test_process_subject_motion_integration(tmp_path):
    """Integration test for process_subject_motion with mock data."""
    # Create a fake motion file
    motion_file = os.path.join(tmp_path, "SUBJ001_movement_params.txt")
    motion_data = np.zeros((10, 6))
    motion_data[1:, 0] = 0.25 * np.arange(1, 10) # High motion
    np.savetxt(motion_file, motion_data)
    
    # Create a fake NIfTI path (just for the name)
    nifti_path = os.path.join(tmp_path, "SUBJ001.nii.gz")
    # We don't need a real NIfTI, just the path to derive the sidecar name
    # But our function looks for sidecar in the same dir
    # Let's rename the motion file to match the expected pattern
    expected_motion_file = os.path.join(tmp_path, "SUBJ001_movement_params.txt")
    # It's already named correctly for the logic in load_motion_params_from_nifti
    
    # Mock the load function to use our temp file directly if needed, 
    # but our logic searches the directory.
    # Let's ensure the file is named correctly for the subject
    # The function load_motion_params_from_nifti looks for <base>_movement_params.txt
    # So if nifti_path is .../SUBJ001.nii.gz, base is .../SUBJ001
    # It looks for .../SUBJ001_movement_params.txt
    # We created that.
    
    # We need to mock the file reading or ensure the path logic works
    # Since we can't easily create a NIfTI, we'll mock the loader
    with patch('code.utils.motion.load_motion_params_from_nifti') as mock_loader:
        mock_loader.return_value = motion_data
        
        should_exclude, mean_fd = process_subject_motion("SUBJ001", nifti_path, threshold=0.2)
        
        assert should_exclude is True
        assert mean_fd > 0.2
        
        # Check log file
        log_file = os.path.join(tmp_path, "exclusion_log.csv")
        # Note: The real function writes to data/processed/exclusion_log.csv
        # We need to mock get_exclusion_log_path to return our temp file
        # But for this test, let's just verify the logic path
        # The actual file writing is tested in test_generate_exclusion_log

def test_run_motion_filtering_pipeline():
    """Test the full pipeline with mock data."""
    subjects = ["SUBJ001", "SUBJ002", "SUBJ003"]
    
    # Mock data: SUBJ001 low motion, SUBJ002 high motion, SUBJ003 high motion
    mock_fds = {
        "SUBJ001": 0.1,
        "SUBJ002": 0.25,
        "SUBJ003": 0.30
    }
    
    with patch('code.utils.motion.process_subject_motion') as mock_process:
        def side_effect(sub_id, *args, **kwargs):
            fd = mock_fds[sub_id]
            return (fd > 0.2), fd
        
        mock_process.side_effect = side_effect
        
        valid, all_fds = run_motion_filtering_pipeline(
            subjects, 
            {s: "/fake/path.nii" for s in subjects},
            threshold=0.2
        )
        
        assert "SUBJ001" in valid
        assert "SUBJ002" not in valid
        assert "SUBJ003" not in valid
        assert len(valid) == 1
        assert np.isclose(all_fds["SUBJ001"], 0.1)
        assert np.isclose(all_fds["SUBJ002"], 0.25)
        assert np.isclose(all_fds["SUBJ003"], 0.30)
