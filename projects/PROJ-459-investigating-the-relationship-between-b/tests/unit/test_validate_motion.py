import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from data.validate import exclude_subjects_by_motion, DataValidationError
from config import get_processed_path, get_derived_path

@pytest.fixture
def mock_confounds_dir(tmp_path):
    """Create a temporary directory with mock confounds files."""
    confounds_dir = tmp_path / "confounds"
    confounds_dir.mkdir()
    return confounds_dir

def create_mock_confounds(path, fd_values):
    """Helper to create a mock confounds TSV file."""
    df = pd.DataFrame({
        'framewise_displacement': fd_values,
        'trans_x': np.zeros(len(fd_values)),
        'trans_y': np.zeros(len(fd_values)),
        'trans_z': np.zeros(len(fd_values)),
    })
    df.to_csv(path, sep='\t', index=False)

def test_exclude_subjects_by_motion_all_pass(mock_confounds_dir):
    """Test that subjects with mean FD <= threshold are retained."""
    subjects = ['sub-01', 'sub-02']
    
    # Create confounds with low FD
    create_mock_confounds(mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv', [0.1, 0.2, 0.15])
    create_mock_confounds(mock_confounds_dir / 'sub-sub-02_desc-confounds_timeseries.tsv', [0.3, 0.25, 0.2])
    
    valid, stats, exclusions = exclude_subjects_by_motion(
        subjects, 
        confounds_dir=mock_confounds_dir, 
        threshold_mm=0.5
    )
    
    assert len(valid) == 2
    assert 'sub-01' in valid
    assert 'sub-02' in valid
    assert len(exclusions) == 0
    assert stats['sub-01'] < 0.5
    assert stats['sub-02'] < 0.5

def test_exclude_subjects_by_motion_all_fail(mock_confounds_dir):
    """Test that subjects with mean FD > threshold are excluded."""
    subjects = ['sub-01', 'sub-02']
    
    # Create confounds with high FD
    create_mock_confounds(mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv', [0.8, 0.9, 0.85])
    create_mock_confounds(mock_confounds_dir / 'sub-sub-02_desc-confounds_timeseries.tsv', [0.6, 0.7, 0.65])
    
    with pytest.raises(DataValidationError) as exc_info:
        exclude_subjects_by_motion(
            subjects, 
            confounds_dir=mock_confounds_dir, 
            threshold_mm=0.5
        )
    
    assert "No subjects passed" in str(exc_info.value)
    assert exc_info.value.code == "ERR_UNDERPOWERED"

def test_exclude_subjects_by_motion_mixed(mock_confounds_dir):
    """Test mixed pass/fail scenario."""
    subjects = ['sub-01', 'sub-02', 'sub-03']
    
    create_mock_confounds(mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv', [0.1, 0.1, 0.1])
    create_mock_confounds(mock_confounds_dir / 'sub-sub-02_desc-confounds_timeseries.tsv', [0.8, 0.8, 0.8])
    create_mock_confounds(mock_confounds_dir / 'sub-sub-03_desc-confounds_timeseries.tsv', [0.4, 0.4, 0.4])
    
    valid, stats, exclusions = exclude_subjects_by_motion(
        subjects, 
        confounds_dir=mock_confounds_dir, 
        threshold_mm=0.5
    )
    
    assert len(valid) == 2
    assert 'sub-01' in valid
    assert 'sub-03' in valid
    assert 'sub-02' not in valid
    assert 'sub-02' in exclusions
    assert 'high_motion' in exclusions['sub-02']

def test_exclude_subjects_by_motion_missing_file(mock_confounds_dir):
    """Test handling of missing confounds file."""
    subjects = ['sub-01', 'sub-02']
    
    # Only create file for sub-01
    create_mock_confounds(mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv', [0.1, 0.1, 0.1])
    
    valid, stats, exclusions = exclude_subjects_by_motion(
        subjects, 
        confounds_dir=mock_confounds_dir, 
        threshold_mm=0.5
    )
    
    assert len(valid) == 1
    assert 'sub-01' in valid
    assert 'sub-02' in exclusions
    assert exclusions['sub-02'] == 'missing_confounds'

def test_exclude_subjects_by_motion_missing_fd_column(mock_confounds_dir):
    """Test handling of missing FD column."""
    subjects = ['sub-01']
    
    path = mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv'
    df = pd.DataFrame({
        'trans_x': [0.1, 0.1, 0.1],
        'trans_y': [0.1, 0.1, 0.1],
    })
    df.to_csv(path, sep='\t', index=False)
    
    valid, stats, exclusions = exclude_subjects_by_motion(
        subjects, 
        confounds_dir=mock_confounds_dir, 
        threshold_mm=0.5
    )
    
    assert len(valid) == 0
    assert 'sub-01' in exclusions
    assert 'missing_fd_column' in exclusions['sub-01']

def test_exclude_subjects_by_motion_nan_handling(mock_confounds_dir):
    """Test handling of NaN values in FD column."""
    subjects = ['sub-01']
    
    path = mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv'
    df = pd.DataFrame({
        'framewise_displacement': [0.1, np.nan, 0.15],
    })
    df.to_csv(path, sep='\t', index=False)
    
    valid, stats, exclusions = exclude_subjects_by_motion(
        subjects, 
        confounds_dir=mock_confounds_dir, 
        threshold_mm=0.5
    )
    
    assert len(valid) == 1
    assert stats['sub-01'] == pytest.approx(0.125)  # mean of [0.1, 0.15]

def test_exclude_subjects_by_motion_all_nan(mock_confounds_dir):
    """Test handling of all NaN values in FD column."""
    subjects = ['sub-01']
    
    path = mock_confounds_dir / 'sub-sub-01_desc-confounds_timeseries.tsv'
    df = pd.DataFrame({
        'framewise_displacement': [np.nan, np.nan, np.nan],
    })
    df.to_csv(path, sep='\t', index=False)
    
    valid, stats, exclusions = exclude_subjects_by_motion(
        subjects, 
        confounds_dir=mock_confounds_dir, 
        threshold_mm=0.5
    )
    
    assert len(valid) == 0
    assert 'sub-01' in exclusions
    assert exclusions['sub-01'] == 'all_fd_nan'