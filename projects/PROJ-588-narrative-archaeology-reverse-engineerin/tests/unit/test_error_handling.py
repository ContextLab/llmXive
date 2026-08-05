import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

from code.data.error_handling import (
    calculate_motion_metrics,
    check_motion_artifacts,
    log_error,
    handle_subject_error,
    get_error_summary,
    clear_error_log
)

class TestCalculateMotionMetrics:
    def test_basic_motion_calculation(self):
        # Create synthetic motion data
        # 10 timepoints, 3 translations (x, y, z)
        translations = np.array([
            [0.0, 0.0, 0.0],
            [0.5, 0.0, 0.0],
            [0.0, 0.5, 0.0],
            [0.0, 0.0, 0.5],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [2.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 2.0]
        ])

        # 10 timepoints, 3 rotations (roll, pitch, yaw) in radians
        rotations = np.array([
            [0.0, 0.0, 0.0],
            [0.01, 0.0, 0.0],
            [0.0, 0.01, 0.0],
            [0.0, 0.0, 0.01],
            [0.02, 0.0, 0.0],
            [0.0, 0.02, 0.0],
            [0.0, 0.0, 0.02],
            [0.05, 0.0, 0.0],
            [0.0, 0.05, 0.0],
            [0.0, 0.0, 0.05]
        ])

        metrics = calculate_motion_metrics(translations, rotations)

        assert "max_displacement_mm" in metrics
        assert "mean_displacement_mm" in metrics
        assert "max_rotation_deg" in metrics
        assert "mean_rotation_deg" in metrics
        assert "framedrops" in metrics
        assert metrics["max_displacement_mm"] > 0.0
        assert metrics["max_rotation_deg"] > 0.0

    def test_zero_motion(self):
        translations = np.zeros((10, 3))
        rotations = np.zeros((10, 3))

        metrics = calculate_motion_metrics(translations, rotations)

        assert metrics["max_displacement_mm"] == 0.0
        assert metrics["mean_displacement_mm"] == 0.0
        assert metrics["max_rotation_deg"] == 0.0
        assert metrics["framedrops"] == 0

    def test_mismatched_shapes(self):
        translations = np.zeros((10, 3))
        rotations = np.zeros((5, 3)) # Mismatch

        with pytest.raises(ValueError):
            calculate_motion_metrics(translations, rotations)

class TestCheckMotionArtifacts:
    def test_acceptable_motion(self):
        metrics = {
            "max_displacement_mm": 1.5,
            "mean_displacement_mm": 0.5,
            "max_rotation_deg": 2.0,
            "mean_rotation_deg": 0.5,
            "framedrops": 2,
            "total_frames": 100,
            "motion_threshold_mm": 3.0
        }

        is_valid, reason = check_motion_artifacts(metrics)
        assert is_valid is True
        assert "acceptable" in reason.lower()

    def test_excessive_displacement(self):
        metrics = {
            "max_displacement_mm": 5.0, # Exceeds default 3.0
            "mean_displacement_mm": 1.0,
            "max_rotation_deg": 1.0,
            "mean_rotation_deg": 0.5,
            "framedrops": 2,
            "total_frames": 100
        }

        is_valid, reason = check_motion_artifacts(metrics)
        assert is_valid is False
        assert "exceeds" in reason.lower()

    def test_excessive_framedrops(self):
        metrics = {
            "max_displacement_mm": 1.0,
            "mean_displacement_mm": 0.5,
            "max_rotation_deg": 1.0,
            "mean_rotation_deg": 0.5,
            "framedrops": 30, # 30% of 100, > 20%
            "total_frames": 100
        }

        is_valid, reason = check_motion_artifacts(metrics)
        assert is_valid is False
        assert "censoring" in reason.lower()

class TestLogError:
    def test_log_error_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_errors.log"
            details = {"motion_mm": 4.5, "framedrops": 5}

            log_error(log_path, "sub-001", "MOTION_ARTIFACT", details)

            assert log_path.exists()
            with open(log_path, 'r') as f:
                line = f.readline()
                entry = json.loads(line)

            assert entry["subject_id"] == "sub-001"
            assert entry["error_code"] == "MOTION_ARTIFACT"
            assert entry["motion_mm"] == 4.5
            assert "timestamp" in entry

    def test_log_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist yet
            nested_path = Path(tmpdir) / "deep" / "nested" / "path" / "errors.log"

            log_error(nested_path, "sub-002", "MISSING_FILE", {})

            assert nested_path.exists()

class TestHandleSubjectError:
    def test_skip_on_motion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "errors.log"
            metrics = {
                "max_displacement_mm": 5.0,
                "framedrops": 5,
                "total_frames": 100
            }

            should_skip = handle_subject_error(
                "sub-003",
                "MOTION_ARTIFACT",
                metrics=metrics,
                error_log_path=log_path
            )

            assert should_skip is True
            assert log_path.exists()

    def test_no_skip_on_valid_motion(self):
        metrics = {
            "max_displacement_mm": 1.0,
            "framedrops": 0,
            "total_frames": 100
        }

        should_skip = handle_subject_error("sub-004", "MOTION_ARTIFACT", metrics=metrics)
        assert should_skip is False

    def test_log_other_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "errors.log"

            should_skip = handle_subject_error(
                "sub-005",
                "PREPROCESSING_FAILED",
                error_log_path=log_path
            )

            assert should_skip is True
            assert log_path.exists()

class TestGetErrorSummary:
    def test_empty_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "nonexistent.log"
            summary = get_error_summary(log_path)

            assert summary["total_errors"] == 0
            assert summary["by_code"] == {}
            assert summary["subjects"] == []

    def test_populated_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "errors.log"

            # Write some fake errors
            with open(log_path, 'w') as f:
                f.write(json.dumps({"subject_id": "sub-001", "error_code": "MOTION"}) + '\n')
                f.write(json.dumps({"subject_id": "sub-001", "error_code": "MISSING"}) + '\n')
                f.write(json.dumps({"subject_id": "sub-002", "error_code": "MOTION"}) + '\n')

            summary = get_error_summary(log_path)

            assert summary["total_errors"] == 3
            assert summary["by_code"]["MOTION"] == 2
            assert summary["by_code"]["MISSING"] == 1
            assert "sub-001" in summary["subjects"]
            assert "sub-002" in summary["subjects"]

class TestClearErrorLog:
    def test_clear_existing_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "errors.log"
            log_path.write_text("test content")

            clear_error_log(log_path)

            assert not log_path.exists()

    def test_clear_nonexistent_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "nonexistent.log"

            # Should not raise
            clear_error_log(log_path)