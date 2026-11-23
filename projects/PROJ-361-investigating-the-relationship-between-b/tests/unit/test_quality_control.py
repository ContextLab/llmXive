"""
Unit tests for motion quality control logic (T015).
"""

import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from utils.quality_control import calculate_mean_fd, run_quality_control, PreprocessingError

def test_calculate_mean_fd_valid_file():
    """Test calculation of mean FD from a valid confounds file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conf_path = Path(tmpdir) / "confounds.tsv"
        # Create a mock confounds file with known FD values
        data = {
            'framewise_displacement': [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        df = pd.DataFrame(data)
        df.to_csv(conf_path, sep='\t', index=False)

        mean_fd = calculate_mean_fd(conf_path)
        expected_mean = 0.3  # (0.1+0.2+0.3+0.4+0.5)/5
        assert abs(mean_fd - expected_mean) < 1e-6

def test_calculate_mean_fd_missing_column():
    """Test that ValueError is raised if column is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conf_path = Path(tmpdir) / "confounds.tsv"
        data = {
            'trans_x': [0.1, 0.2]
        }
        df = pd.DataFrame(data)
        df.to_csv(conf_path, sep='\t', index=False)

        with pytest.raises(ValueError, match="Column 'framewise_displacement' missing"):
            calculate_mean_fd(conf_path)

def test_calculate_mean_fd_empty_values():
    """Test that ValueError is raised if no valid values exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        conf_path = Path(tmpdir) / "confounds.tsv"
        data = {
            'framewise_displacement': [None, None, None]
        }
        df = pd.DataFrame(data)
        df.to_csv(conf_path, sep='\t', index=False)

        with pytest.raises(ValueError, match="No valid FD values found"):
            calculate_mean_fd(conf_path)

def test_run_quality_control_integration():
    """Test the full QC pipeline with mock data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        out_dir = Path(tmpdir) / "processed"
        raw_dir.mkdir()

        # Create mock subject directories and confounds
        # Subject A: Low motion (Included)
        sub_a_dir = raw_dir / "sub-01" / "func"
        sub_a_dir.mkdir(parents=True)
        conf_a = sub_a_dir / "sub-01_desc-confounds_timeseries.tsv"
        pd.DataFrame({'framewise_displacement': [0.1, 0.1, 0.1]}).to_csv(conf_a, sep='\t', index=False)

        # Subject B: High motion (Excluded)
        sub_b_dir = raw_dir / "sub-02" / "func"
        sub_b_dir.mkdir(parents=True)
        conf_b = sub_b_dir / "sub-02_desc-confounds_timeseries.tsv"
        pd.DataFrame({'framewise_displacement': [0.6, 0.7, 0.8]}).to_csv(conf_b, sep='\t', index=False)

        # Run QC
        result = run_quality_control(raw_data_dir=raw_dir, output_dir=out_dir)

        assert len(result['included_subjects']) == 1
        assert 'sub-01' in result['included_subjects']
        assert len(result['excluded_subjects']) == 1
        assert 'sub-02' in result['excluded_subjects']

        # Check file outputs
        assert (out_dir / "qc_motion_report.csv").exists()
        assert (out_dir / "excluded_subjects.txt").exists()

        with open(out_dir / "excluded_subjects.txt", 'r') as f:
            assert "sub-02" in f.read()