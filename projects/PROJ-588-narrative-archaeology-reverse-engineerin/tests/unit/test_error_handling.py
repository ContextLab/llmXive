"""
Unit tests for error handling infrastructure.
"""
import numpy as np
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

# Mock config for testing
import sys
from unittest.mock import patch, MagicMock

# Create a mock config module
mock_config = MagicMock()
mock_config.DATA_DIR = tempfile.mkdtemp()
mock_config.MOTION_THRESHOLD_MM = 0.5

sys.modules['code.config'] = mock_config

from code.data.error_handling import (
    calculate_motion_metrics,
    check_motion_artifacts,
    log_error,
    handle_subject_error,
    get_error_summary,
    clear_error_log
)


class TestCalculateMotionMetrics:
    def test_empty_arrays(self):
        """Test with empty displacement/rotation arrays."""
        displacement = np.array([]).reshape(0, 3)
        rotation = np.array([]).reshape(0, 3)

        metrics = calculate_motion_metrics(displacement, rotation)

        assert metrics["mean_displacement"] == 0.0
        assert metrics["max_displacement"] == 0.0
        assert metrics["mean_rotation_mm"] == 0.0
        assert metrics["max_rotation_mm"] == 0.0
        assert len(metrics["framewise_displacement"]) == 0

    def test_single_volume(self):
        """Test with single volume (no FD calculation possible)."""
        displacement = np.array([[1.0, 0.5, 0.2]])
        rotation = np.array([[0.01, 0.02, 0.015]])

        metrics = calculate_motion_metrics(displacement, rotation, voxel_size=3.0)

        assert metrics["mean_displacement"] == pytest.approx(np.sqrt(1.0**2 + 0.5**2 + 0.2**2))
        assert metrics["mean_rotation_mm"] > 0.0
        # FD requires at least 2 volumes, so should be empty
        assert len(metrics["framewise_displacement"]) == 0

    def test_multiple_volumes(self):
        """Test with multiple volumes to verify FD calculation."""
        displacement = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        rotation = np.array([
            [0.0, 0.0, 0.0],
            [0.01, 0.0, 0.0],
            [0.0, 0.01, 0.0]
        ])

        metrics = calculate_motion_metrics(displacement, rotation, voxel_size=3.0)

        assert len(metrics["framewise_displacement"]) == 2  # N-1 for N volumes
        assert metrics["mean_displacement"] > 0.0
        assert metrics["max_displacement"] > 0.0


class TestCheckMotionArtifacts:
    def test_below_threshold(self):
        """Test subject with motion below threshold."""
        displacement = np.array([[0.1, 0.1, 0.1]] * 100)
        rotation = np.array([[0.001, 0.001, 0.001]] * 100)

        result = check_motion_artifacts(displacement, rotation, threshold_mm=0.5)

        assert result["is_rejected"] is False
        assert result["reason"] is None

    def test_mean_fd_exceeds_threshold(self):
        """Test subject rejected due to high mean FD."""
        displacement = np.array([[0.6, 0.0, 0.0]] * 100)
        rotation = np.array([[0.0, 0.0, 0.0]] * 100)

        result = check_motion_artifacts(displacement, rotation, threshold_mm=0.5)

        assert result["is_rejected"] is True
        assert "Mean FD" in result["reason"]

    def test_max_fd_exceeds_3x_threshold(self):
        """Test subject rejected due to extreme single-frame motion."""
        displacement = np.zeros((100, 3))
        displacement[50] = [2.0, 0.0, 0.0]  # Spike at frame 50
        rotation = np.zeros((100, 3))

        result = check_motion_artifacts(displacement, rotation, threshold_mm=0.5)

        assert result["is_rejected"] is True
        assert "Maximum FD" in result["reason"]

    def test_high_motion_ratio(self):
        """Test subject rejected due to high proportion of motion frames."""
        displacement = np.array([[0.6, 0.0, 0.0]] * 50 + [[0.1, 0.0, 0.0]] * 50)
        rotation = np.zeros((100, 3))

        result = check_motion_artifacts(displacement, rotation, threshold_mm=0.5)

        assert result["is_rejected"] is True
        assert "High motion ratio" in result["reason"]


class TestLogError:
    def test_log_error_creates_entry(self):
        """Test that logging an error creates a valid JSON entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.DATA_DIR = tmpdir
            clear_error_log()  # Ensure clean state

            log_error(
                subject_id="sub-001",
                error_code="MOTION_ARTIFACT",
                error_message="Excessive motion detected",
                motion_mm=1.2
            )

            errors = get_error_summary()
            assert len(errors) == 1

            entry = errors[0]
            assert entry["subject_id"] == "sub-001"
            assert entry["error_code"] == "MOTION_ARTIFACT"
            assert entry["motion_mm"] == 1.2
            assert "timestamp" in entry
            assert "error_message" in entry

    def test_log_error_with_additional_data(self):
        """Test logging with additional context data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.DATA_DIR = tmpdir
            clear_error_log()

            log_error(
                subject_id="sub-002",
                error_code="PREPROCESSING_FAILED",
                error_message="fMRIPrep failed",
                additional_data={"return_code": 1, "command": "fmriprep ..."},
                motion_mm=0.0
            )

            errors = get_error_summary()
            assert len(errors) == 1
            assert errors[0]["return_code"] == 1
            assert errors[0]["command"] == "fmriprep ..."


class TestHandleSubjectError:
    def test_handle_and_skip(self):
        """Test that handle_subject_error logs and skips by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.DATA_DIR = tmpdir
            clear_error_log()

            motion_metrics = {"mean_displacement": 1.5}
            skipped = handle_subject_error(
                subject_id="sub-003",
                error_code="MOTION_ARTIFACT",
                error_message="Motion too high",
                motion_metrics=motion_metrics,
                skip=True
            )

            assert skipped is True
            errors = get_error_summary()
            assert len(errors) == 1
            assert errors[0]["subject_id"] == "sub-003"

    def test_handle_no_skip(self):
        """Test that handle_subject_error logs but doesn't skip when skip=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.DATA_DIR = tmpdir
            clear_error_log()

            skipped = handle_subject_error(
                subject_id="sub-004",
                error_code="WARNING",
                error_message="Minor issue, continuing",
                skip=False
            )

            assert skipped is False
            errors = get_error_summary()
            assert len(errors) == 1


class TestClearErrorLog:
    def test_clear_removes_file(self):
        """Test that clear_error_log removes the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_config.DATA_DIR = tmpdir
            clear_error_log()

            log_error("sub-001", "TEST", "Test error")
            assert Path(mock_config.DATA_DIR, "errors.log").exists()

            clear_error_log()
            assert not Path(mock_config.DATA_DIR, "errors.log").exists()