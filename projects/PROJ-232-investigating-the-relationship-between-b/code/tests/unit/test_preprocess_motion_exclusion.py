import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.data.preprocess import (
    calculate_framewise_displacement,
    exclude_high_motion_subjects,
    ensure_directories,
    save_run_log,
    FD_THRESHOLD
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure mimicking the project data layout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create directory structure
        preprocessing_dir = base_path / "preprocessing"
        preprocessing_dir.mkdir()
        
        # Create a mock subject directory
        sub_dir = preprocessing_dir / "sub-01" / "func"
        sub_dir.mkdir(parents=True)
        
        # Create a mock confounds.tsv with low motion
        # Columns: trans_x, trans_y, trans_z, rot_x, rot_y, rot_z
        # We want mean FD < 0.5
        # FD = |Δx| + |Δy| + |Δz| + |Δrot|*50
        # Let's make small changes: 0.1, 0.1, 0.1, 0.001, 0.001, 0.001
        # FD per step ≈ 0.3 + 0.15 = 0.45 (avg over time)
        data = {
            'trans_x': [0.0, 0.1, 0.15, 0.2, 0.25, 0.3],
            'trans_y': [0.0, 0.1, 0.15, 0.2, 0.25, 0.3],
            'trans_z': [0.0, 0.1, 0.15, 0.2, 0.25, 0.3],
            'rot_x': [0.0, 0.001, 0.0015, 0.002, 0.0025, 0.003],
            'rot_y': [0.0, 0.001, 0.0015, 0.002, 0.0025, 0.003],
            'rot_z': [0.0, 0.001, 0.0015, 0.002, 0.0025, 0.003],
            'csf': [0.0] * 6,
            'white_matter': [0.0] * 6
        }
        df = pd.DataFrame(data)
        confounds_path = sub_dir / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        df.to_csv(confounds_path, sep='\t', index=False)
        
        # Create a second subject with high motion
        sub2_dir = preprocessing_dir / "sub-02" / "func"
        sub2_dir.mkdir(parents=True)
        data_high = {
            'trans_x': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], # Large jumps
            'trans_y': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            'trans_z': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            'rot_x': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            'rot_y': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            'rot_z': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            'csf': [0.0] * 6,
            'white_matter': [0.0] * 6
        }
        df_high = pd.DataFrame(data_high)
        confounds_path_high = sub2_dir / "sub-02_task-rest_desc-confounds_timeseries.tsv"
        df_high.to_csv(confounds_path_high, sep='\t', index=False)
        
        yield base_path

def test_calculate_framewise_displacement(temp_data_dir):
    """Test that FD is calculated correctly for a subject."""
    # Test low motion subject
    fd_low = calculate_framewise_displacement("01", base_path=temp_data_dir)
    assert fd_low is not None
    assert fd_low < 0.5  # Should be low
    
    # Test high motion subject
    fd_high = calculate_framewise_displacement("02", base_path=temp_data_dir)
    assert fd_high is not None
    assert fd_high > 0.5  # Should be high

def test_exclude_high_motion_subjects(temp_data_dir):
    """Test that subjects are correctly included/excluded based on FD threshold."""
    subjects = ["01", "02"]
    included, excluded = exclude_high_motion_subjects(subjects, base_path=temp_data_dir)
    
    assert "01" in included
    assert "02" in excluded
    assert len(included) == 1
    assert len(excluded) == 1

def test_exclude_high_motion_subjects_no_files(temp_data_dir):
    """Test behavior when confounds file is missing."""
    subjects = ["03"] # Subject 03 does not exist
    included, excluded = exclude_high_motion_subjects(subjects, base_path=temp_data_dir)
    
    assert len(included) == 0
    assert len(excluded) == 1
    assert "03" in excluded

def test_exclude_high_motion_subjects_all_high(temp_data_dir):
    """Test behavior when all subjects have high motion."""
    subjects = ["02"]
    included, excluded = exclude_high_motion_subjects(subjects, base_path=temp_data_dir)
    
    assert len(included) == 0
    assert len(excluded) == 1
    assert "02" in excluded
