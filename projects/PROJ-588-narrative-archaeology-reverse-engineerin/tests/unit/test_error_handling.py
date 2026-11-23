"""
Unit tests for code/data/error_handling.py
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

import pytest

# Import the module under test
from code.data.error_handling import (
    calculate_motion_metrics,
    check_motion_artifacts,
    log_error,
    handle_subject_error,
    get_error_summary,
    clear_error_log
)
import code.config as config


class TestCalculateMotionMetrics:
    def test_calculate_fd_from_trans_rot(self, tmp_path):
        """Test FD calculation from translation/rotation columns."""
        # Create a mock confounds file
        confounds_file = tmp_path / "sub-01_desc-confounds_regressors.tsv"
        
        # Generate synthetic motion data
        n_timepoints = 100
        data = {
            'trans_x': np.random.randn(n_timepoints) * 0.1,
            'trans_y': np.random.randn(n_timepoints) * 0.1,
            'trans_z': np.random.randn(n_timepoints) * 0.1,
            'rot_x': np.random.randn(n_timepoints) * 0.01,
            'rot_y': np.random.randn(n_timepoints) * 0.01,
            'rot_z': np.random.randn(n_timepoints) * 0.01,
        }
        df = pd.DataFrame(data)
        df.to_csv(confounds_file, sep='\t', index=False)

        metrics = calculate_motion_metrics("sub-01", tmp_path)

        assert 'mean_fd' in metrics
        assert 'max_fd' in metrics
        assert 'mean_dvars' in metrics
        assert metrics['mean_fd'] >= 0
        assert metrics['max_fd'] >= metrics['mean_fd']

    def test_calculate_fd_from_existing_column(self, tmp_path):
        """Test FD calculation when 'framewise_displacement' column exists."""
        confounds_file = tmp_path / "sub-01_desc-confounds_regressors.tsv"
        
        n_timepoints = 50
        data = {
            'framewise_displacement': np.abs(np.random.randn(n_timepoints) * 0.2),
            'dvars': np.abs(np.random.randn(n_timepoints) * 0.5),
        }
        df = pd.DataFrame(data)
        df.to_csv(confounds_file, sep='\t', index=False)

        metrics = calculate_motion_metrics("sub-01", tmp_path)

        assert metrics['mean_fd'] > 0
        assert metrics['mean_dvars'] > 0

    def test_missing_confounds_file(self, tmp_path):
        """Test that FileNotFoundError is raised if file is missing."""
        with pytest.raises(FileNotFoundError):
            calculate_motion_metrics("sub-01", tmp_path)


class TestCheckMotionArtifacts:
    def test_pass_motion_check(self):
        """Test that low motion passes the check."""
        metrics = {
            'mean_fd': 0.1,
            'pct_high_fd': 5.0
        }
        assert check_motion_artifacts(metrics, threshold_mm=0.5) is False

    def test_fail_mean_fd(self):
        """Test that high mean FD fails the check."""
        metrics = {
            'mean_fd': 0.6,
            'pct_high_fd': 5.0
        }
        assert check_motion_artifacts(metrics, threshold_mm=0.5) is True

    def test_fail_pct_high_fd(self):
        """Test that high percentage of high motion fails the check."""
        metrics = {
            'mean_fd': 0.2,
            'pct_high_fd': 25.0
        }
        assert check_motion_artifacts(metrics, threshold_mm=0.5) is True


class TestLogError:
    def test_log_error_creates_file(self, tmp_path, monkeypatch):
        """Test that log_error creates the file and writes JSON."""
        # Monkeypatch config.DATA_DIR to use tmp_path
        monkeypatch.setattr(config, 'DATA_DIR', str(tmp_path))

        log_error("sub-01", "MOTION_ARTIFACT", "High motion detected", motion_mm=0.8)

        log_file = tmp_path / "errors.log"
        assert log_file.exists()

        with open(log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)
            
        assert entry['subject_id'] == "sub-01"
        assert entry['error_code'] == "MOTION_ARTIFACT"
        assert entry['motion_mm'] == 0.8
        assert 'timestamp' in entry

    def test_log_error_appends(self, tmp_path, monkeypatch):
        """Test that log_error appends to existing log."""
        monkeypatch.setattr(config, 'DATA_DIR', str(tmp_path))

        log_error("sub-01", "ERR1", "Msg1")
        log_error("sub-02", "ERR2", "Msg2")

        log_file = tmp_path / "errors.log"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2


class TestHandleSubjectError:
    def test_handle_subject_error_raises(self, tmp_path, monkeypatch):
        """Test that handle_subject_error logs and raises RuntimeError."""
        monkeypatch.setattr(config, 'DATA_DIR', str(tmp_path))

        with pytest.raises(RuntimeError) as exc_info:
            handle_subject_error("sub-01", "MOTION", "Too much head movement", motion_mm=0.9)

        assert "sub-01" in str(exc_info.value)
        assert "MOTION" in str(exc_info.value)


class TestGetErrorSummary:
    def test_get_error_summary(self, tmp_path, monkeypatch):
        """Test summary generation."""
        monkeypatch.setattr(config, 'DATA_DIR', str(tmp_path))

        log_error("sub-01", "MOTION", "High FD")
        log_error("sub-02", "MOTION", "High FD")
        log_error("sub-03", "FILE_NOT_FOUND", "Missing file")

        summary = get_error_summary()

        assert summary['total_errors'] == 3
        assert summary['by_code']['MOTION'] == 2
        assert summary['by_code']['FILE_NOT_FOUND'] == 1

    def test_empty_log(self, tmp_path, monkeypatch):
        """Test summary with no log file."""
        monkeypatch.setattr(config, 'DATA_DIR', str(tmp_path))
        
        summary = get_error_summary()
        assert summary['total_errors'] == 0
        assert summary['by_code'] == {}


class TestClearErrorLog:
    def test_clear_error_log(self, tmp_path, monkeypatch):
        """Test clearing the log file."""
        monkeypatch.setattr(config, 'DATA_DIR', str(tmp_path))

        log_error("sub-01", "MOTION", "High FD")
        assert (tmp_path / "errors.log").exists()

        clear_error_log()
        assert not (tmp_path / "errors.log").exists()