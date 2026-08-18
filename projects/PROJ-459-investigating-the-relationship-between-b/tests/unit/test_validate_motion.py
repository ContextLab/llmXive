import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from data.validate import exclude_subjects_by_motion, DataValidationError

def create_confounds_file(path, fd_values):
    """Helper to create a mock fMRIPrep confounds file."""
    df = pd.DataFrame({
        'framewise_displacement': fd_values,
        'trans_x': np.zeros_like(fd_values),
        'trans_y': np.zeros_like(fd_values),
        'trans_z': np.zeros_like(fd_values),
        'rot_x': np.zeros_like(fd_values),
        'rot_y': np.zeros_like(fd_values),
        'rot_z': np.zeros_like(fd_values)
    })
    df.to_csv(path, sep='\t', index=False)

def test_exclude_subjects_by_motion_normal():
    """Test that subjects with low motion are not excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a confounds file with low motion (all FD < 0.1)
        fd_vals = [0.05] * 100
        fpath = Path(tmpdir) / "sub-01_desc-confounds_timeseries.tsv"
        create_confounds_file(fpath, fd_vals)
        
        excluded = exclude_subjects_by_motion(Path(tmpdir))
        
        assert "01" not in excluded
        assert len(excluded) == 0

def test_exclude_subjects_by_motion_high_fraction():
    """Test that subjects with >10% high motion are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a confounds file where 15% of points have FD > 0.5
        # 100 points total, 15 high
        fd_vals = [0.6] * 15 + [0.1] * 85
        # Shuffle to simulate real distribution
        import random
        random.shuffle(fd_vals)
        
        fpath = Path(tmpdir) / "sub-02_desc-confounds_timeseries.tsv"
        create_confounds_file(fpath, fd_vals)
        
        excluded = exclude_subjects_by_motion(Path(tmpdir))
        
        assert "02" in excluded
        assert len(excluded) == 1

def test_exclude_subjects_by_motion_edge_case():
    """Test subject exactly at threshold (10% high motion)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 100 points, 10 high (exactly 10%)
        # Threshold is > 0.10, so 0.10 should NOT be excluded
        fd_vals = [0.6] * 10 + [0.1] * 90
        fpath = Path(tmpdir) / "sub-03_desc-confounds_timeseries.tsv"
        create_confounds_file(fpath, fd_vals)
        
        excluded = exclude_subjects_by_motion(Path(tmpdir))
        
        # 10% is not > 10%, so should NOT be excluded
        assert "03" not in excluded

def test_exclude_subjects_by_motion_missing_fd():
    """Test behavior when FD column is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file without FD column
        df = pd.DataFrame({
            'trans_x': [0.1] * 100,
            'trans_y': [0.1] * 100
        })
        fpath = Path(tmpdir) / "sub-04_desc-confounds_timeseries.tsv"
        df.to_csv(fpath, sep='\t', index=False)
        
        excluded = exclude_subjects_by_motion(Path(tmpdir))
        
        # Should skip this subject, not crash, and not exclude
        assert "04" not in excluded

def test_exclude_subjects_by_motion_with_nan():
    """Test handling of NaN values in FD column."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # fMRIPrep often has NaN for first timepoint
        fd_vals = [np.nan] + [0.6] * 15 + [0.1] * 84
        fpath = Path(tmpdir) / "sub-05_desc-confounds_timeseries.tsv"
        create_confounds_file(fpath, fd_vals)
        
        excluded = exclude_subjects_by_motion(Path(tmpdir))
        
        # Should calculate based on valid values only
        # 15 high out of 99 valid = ~15.1% -> exclude
        assert "05" in excluded