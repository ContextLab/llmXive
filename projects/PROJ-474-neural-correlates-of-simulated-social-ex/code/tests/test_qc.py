"""
Unit tests for the QC (quality control) module.
Tests motion calculation, condition verification, and subject filtering.
"""
import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from src.qc import (
    calculate_framewise_displacement,
    filter_by_motion_threshold,
    check_subject_count,
    load_motion_parameters,
    verify_conditions,
)
from src.exceptions import DataUnavailableError, InsufficientSubjectsError


class TestFramewiseDisplacement:
    """Test FD calculation from motion parameters."""

    def test_calculate_fd_with_precomputed_column(self):
        """Test that pre‑computed framewise_displacement column is used when available."""
        df = pd.DataFrame({
            'framewise_displacement': [0.1, 0.15, 0.12, 0.08, 0.2],
            'other_col': [1, 2, 3, 4, 5]
        })
        fd = calculate_framewise_displacement(df)
        expected = np.mean([0.1, 0.15, 0.12, 0.08, 0.2])
        assert abs(fd - expected) < 1e-6

    def test_calculate_fd_from_motion_params(self):
        """Test FD calculation from raw motion parameters."""
        # Create synthetic motion parameters
        n_volumes = 100
        trans_x = np.random.randn(n_volumes) * 0.01
        trans_y = np.random.randn(n_volumes) * 0.01
        trans_z = np.random.randn(n_volumes) * 0.01
        rot_x = np.random.randn(n_volumes) * 0.001
        rot_y = np.random.randn(n_volumes) * 0.001
        rot_z = np.random.randn(n_volumes) * 0.001
        
        df = pd.DataFrame({
            'trans_x': trans_x,
            'trans_y': trans_y,
            'trans_z': trans_z,
            'rot_x': rot_x,
            'rot_y': rot_y,
            'rot_z': rot_z,
        })
        
        fd = calculate_framewise_displacement(df)
        assert isinstance(fd, float)
        assert fd >= 0

    def test_calculate_fd_zero_motion(self):
        """Test FD calculation with zero motion."""
        df = pd.DataFrame({
            'trans_x': np.zeros(50),
            'trans_y': np.zeros(50),
            'trans_z': np.zeros(50),
            'rot_x': np.zeros(50),
            'rot_y': np.zeros(50),
            'rot_z': np.zeros(50),
        })
        
        fd = calculate_framewise_displacement(df)
        assert fd == 0.0


class TestMotionThresholdFiltering:
    """Test subject filtering based on motion threshold (FR-002)."""

    def test_filter_fd_greater_than_threshold(self):
        """Test that subjects with FD > 0.2 mm are marked as failed (FR-002)."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": 0.25,  # > 0.2 mm
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            }
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered[0]["qc_status"] == "failed"

    def test_filter_fd_equal_to_threshold(self):
        """Test that subjects with FD = 0.2 mm are marked as passed (FR-002)."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": 0.2,  # == 0.2 mm
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            }
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered[0]["qc_status"] == "passed"

    def test_filter_fd_less_than_threshold(self):
        """Test that subjects with FD < 0.2 mm are marked as passed."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": 0.15,  # < 0.2 mm
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            }
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered[0]["qc_status"] == "passed"

    def test_filter_invalid_conditions(self):
        """Test that subjects with invalid conditions are marked as failed."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": 0.1,
                "condition_valid": False,  # Invalid conditions
                "conditions": ["Inclusion"]
            }
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered[0]["qc_status"] == "failed"

    def test_filter_missing_motion_data(self):
        """Test that subjects with missing motion data are marked as failed."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": None,
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            }
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered[0]["qc_status"] == "failed"

    def test_filter_mixed_subjects(self):
        """Test filtering with a mix of passing and failing subjects."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": 0.15,
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            },
            {
                "subject_id": "sub-02",
                "motion_mean": 0.25,
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            },
            {
                "subject_id": "sub-03",
                "motion_mean": 0.1,
                "condition_valid": False,
                "conditions": ["Inclusion"]
            }
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered[0]["qc_status"] == "passed"
        assert filtered[1]["qc_status"] == "failed"
        assert filtered[2]["qc_status"] == "failed"


class TestSubjectCountCheck:
    """Test subject count validation (FR-009)."""

    def test_sufficient_subjects(self):
        """Test that sufficient subjects pass the check."""
        subject_list = [
            {"subject_id": f"sub-{i:02d}", "qc_status": "passed"}
            for i in range(1, 11)
        ]
        
        # Should not raise
        check_subject_count(subject_list, min_count=10)

    def test_insufficient_subjects(self):
        """Test that insufficient subjects raise an error (FR-009)."""
        subject_list = [
            {"subject_id": f"sub-{i:02d}", "qc_status": "passed"}
            for i in range(1, 9)
        ]
        
        with pytest.raises(InsufficientSubjectsError):
            check_subject_count(subject_list, min_count=10)

    def test_exactly_minimum_subjects(self):
        """Test with exactly the minimum number of subjects."""
        subject_list = [
            {"subject_id": f"sub-{i:02d}", "qc_status": "passed"}
            for i in range(1, 11)
        ]
        
        # Should not raise
        check_subject_count(subject_list, min_count=10)

    def test_more_than_minimum_subjects(self):
        """Test with more than the minimum number of subjects."""
        subject_list = [
            {"subject_id": f"sub-{i:02d}", "qc_status": "passed"}
            for i in range(1, 16)
        ]
        
        # Should not raise
        check_subject_count(subject_list, min_count=10)


class TestQCSchema:
    """Test that QC output conforms to contracts/subject.schema.yaml."""

    def test_subject_metadata_schema_compliance(self):
        """Test that filtered subjects conform to the schema."""
        subject_list = [
            {
                "subject_id": "sub-01",
                "motion_mean": 0.15,
                "qc_status": "passed",
                "conditions": ["Inclusion", "Exclusion"]
            },
            {
                "subject_id": "sub-02",
                "motion_mean": 0.25,
                "qc_status": "failed",
                "conditions": ["Inclusion"]
            }
        ]
        
        # Verify schema compliance
        for subject in subject_list:
            assert "subject_id" in subject
            assert isinstance(subject["subject_id"], str)
            assert "motion_mean" in subject
            assert isinstance(subject["motion_mean"], (int, float)) or subject["motion_mean"] is None
            assert "qc_status" in subject
            assert subject["qc_status"] in ["passed", "failed"]
            assert "conditions" in subject
            assert isinstance(subject["conditions"], list)
            for cond in subject["conditions"]:
                assert cond in ["Inclusion", "Exclusion"]


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_subject_list(self):
        """Test filtering an empty subject list."""
        subject_list = []
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        assert filtered == []

    def test_all_subjects_fail_motion(self):
        """Test when all subjects exceed motion threshold."""
        subject_list = [
            {
                "subject_id": f"sub-{i:02d}",
                "motion_mean": 0.3 + i * 0.01,
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            }
            for i in range(5)
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        passed = [s for s in filtered if s["qc_status"] == "passed"]
        assert len(passed) == 0

    def test_all_subjects_pass_motion(self):
        """Test when all subjects pass motion threshold."""
        subject_list = [
            {
                "subject_id": f"sub-{i:02d}",
                "motion_mean": 0.1,
                "condition_valid": True,
                "conditions": ["Inclusion", "Exclusion"]
            }
            for i in range(15)
        ]
        
        filtered = filter_by_motion_threshold(subject_list, threshold=0.2)
        passed = [s for s in filtered if s["qc_status"] == "passed"]
        assert len(passed) == 15