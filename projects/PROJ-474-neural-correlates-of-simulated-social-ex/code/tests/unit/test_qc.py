"""
Unit tests for the QC module.
"""
import pytest
import numpy as np
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.qc import (
    load_motion_parameters,
    calculate_framewise_displacement,
    calculate_subject_motion_metrics,
    check_subject_count,
    verify_conditions,
    InsufficientDataError
)

class TestMotionCalculation:
    """Tests for motion parameter loading and FD calculation."""

    def test_load_motion_parameters_valid(self, tmp_path):
        """Test loading valid motion parameters."""
        # Create a temporary motion file
        motion_file = tmp_path / "sub-01_desc-movement.tsv"
        data = np.random.rand(100, 6)
        np.savetxt(motion_file, data, delimiter='\t')

        loaded = load_motion_parameters(motion_file)
        
        assert loaded.shape == (100, 6)
        assert np.allclose(loaded, data)

    def test_load_motion_parameters_insufficient_columns(self, tmp_path):
        """Test that loading fails with insufficient columns."""
        motion_file = tmp_path / "sub-01_desc-movement.tsv"
        data = np.random.rand(100, 3)  # Only 3 columns
        np.savetxt(motion_file, data, delimiter='\t')

        with pytest.raises(ValueError, match="at least 6 columns"):
            load_motion_parameters(motion_file)

    def test_load_motion_parameters_file_not_found(self):
        """Test that loading fails when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_motion_parameters(Path("/nonexistent/file.tsv"))

    def test_calculate_framewise_displacement(self):
        """Test FD calculation with known values."""
        # Create motion parameters with known displacements
        motion = np.zeros((10, 6))
        motion[1:, 0] = 1.0  # 1mm translation in x
        
        fd = calculate_framewise_displacement(motion)
        
        # First row should be 0 (no previous), rest should be 1.0
        assert len(fd) == 9
        assert np.allclose(fd, 1.0)

    def test_calculate_framewise_displacement_rotation(self):
        """Test FD calculation with rotation."""
        # Create motion with rotation (in radians)
        motion = np.zeros((10, 6))
        motion[1:, 3] = 0.001  # Small rotation in x (radians)
        
        fd = calculate_framewise_displacement(motion)
        
        # FD should include rotation component (radius=50mm)
        # 0.001 rad * 50mm = 0.05mm
        expected_fd = 0.05
        assert np.allclose(fd, expected_fd, atol=0.001)

    def test_calculate_framewise_displacement_empty(self):
        """Test FD calculation with insufficient data."""
        motion = np.zeros((1, 6))
        fd = calculate_framewise_displacement(motion)
        
        assert len(fd) == 0

class TestMotionHardStop:
    """Tests for subject count checking."""

    def test_check_subject_count_pass(self):
        """Test that sufficient subjects pass."""
        results = [{"retained": True} for _ in range(15)]
        
        # Should not raise
        check_subject_count(results, min_subjects=10)

    def test_check_subject_count_fail(self):
        """Test that insufficient subjects raise error."""
        results = [{"retained": True} for _ in range(5)]
        
        with pytest.raises(InsufficientDataError, match="Insufficient subjects"):
            check_subject_count(results, min_subjects=10)

    def test_check_subject_count_exact(self):
        """Test boundary condition with exact number."""
        results = [{"retained": True} for _ in range(10)]
        
        # Should not raise
        check_subject_count(results, min_subjects=10)

class TestConditionCompleteness:
    """Tests for condition verification."""

    def test_verify_conditions_both_present(self, tmp_path):
        """Test events file with both conditions."""
        events_file = tmp_path / "sub-01_events.tsv"
        content = """onset	duration	trial_type
        10	2	Inclusion
        30	2	Exclusion"""
        
        with open(events_file, 'w') as f:
            f.write(content)
        
        has_inc, has_exc = verify_conditions(tmp_path, events_file)
        
        assert has_inc is True
        assert has_exc is True

    def test_verify_conditions_missing_inclusion(self, tmp_path):
        """Test events file missing Inclusion condition."""
        events_file = tmp_path / "sub-01_events.tsv"
        content = """onset	duration	trial_type
        10	2	Exclusion
        30	2	Control"""
        
        with open(events_file, 'w') as f:
            f.write(content)
        
        has_inc, has_exc = verify_conditions(tmp_path, events_file)
        
        assert has_inc is False
        assert has_exc is True

    def test_verify_conditions_missing_exclusion(self, tmp_path):
        """Test events file missing Exclusion condition."""
        events_file = tmp_path / "sub-01_events.tsv"
        content = """onset	duration	trial_type
        10	2	Inclusion
        30	2	Control"""
        
        with open(events_file, 'w') as f:
            f.write(content)
        
        has_inc, has_exc = verify_conditions(tmp_path, events_file)
        
        assert has_inc is True
        assert has_exc is False

    def test_verify_conditions_no_file(self, tmp_path):
        """Test when events file doesn't exist."""
        has_inc, has_exc = verify_conditions(tmp_path / "sub-01")
        
        assert has_inc is False
        assert has_exc is False

class TestSubjectMotionMetrics:
    """Tests for subject-level motion metrics."""

    def test_calculate_subject_motion_metrics(self, tmp_path):
        """Test full subject motion metric calculation."""
        # Create directory structure
        func_dir = tmp_path / "sub-01" / "func"
        func_dir.mkdir(parents=True)
        
        # Create motion file
        motion_file = func_dir / "sub-01_desc-movement.tsv"
        data = np.random.rand(100, 6)
        np.savetxt(motion_file, data, delimiter='\t')
        
        config = {"qc": {"motion_threshold": 3.0}}
        
        result = calculate_subject_motion_metrics(tmp_path / "sub-01", config)
        
        assert result is not None
        assert "subject_id" in result
        assert "max_fd" in result
        assert "mean_fd" in result
        assert "retained" in result
        assert isinstance(result["retained"], bool)

    def test_calculate_subject_motion_metrics_no_func_dir(self, tmp_path):
        """Test when functional directory doesn't exist."""
        result = calculate_subject_motion_metrics(tmp_path / "sub-01", {})
        
        assert result is None

    def test_calculate_subject_motion_metrics_no_motion_file(self, tmp_path):
        """Test when motion file doesn't exist."""
        func_dir = tmp_path / "sub-01" / "func"
        func_dir.mkdir(parents=True)
        
        result = calculate_subject_motion_metrics(tmp_path / "sub-01", {})
        
        assert result is None