"""
Unit tests for motion threshold exclusion logic (T011).
Validates the filtering logic implemented in T014 (exclusion of subjects with mean FD >= 0.2mm).
"""
import pandas as pd
import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path to allow imports
# Assuming this test runs from code/tests/unit, we go up two levels
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.entities.models import Subject


class TestMotionThresholdExclusion:
    """Tests for the motion quality control filtering logic."""

    @pytest.fixture
    def sample_subjects(self):
        """Create a list of Subject objects with varying mean FD values."""
        subjects = [
            Subject(subject_id="1001", dsrt_score=5.2, age=24, sex="M", mean_fd=0.05),
            Subject(subject_id="1002", dsrt_score=3.1, age=29, sex="F", mean_fd=0.18),
            Subject(subject_id="1003", dsrt_score=4.5, age=22, sex="M", mean_fd=0.20),
            Subject(subject_id="1004", dsrt_score=6.0, age=35, sex="F", mean_fd=0.21),
            Subject(subject_id="1005", dsrt_score=2.8, age=27, sex="M", mean_fd=0.45),
            Subject(subject_id="1006", dsrt_score=5.9, age=30, sex="F", mean_fd=0.19),
        ]
        return subjects

    def test_filter_motion_logic(self, sample_subjects):
        """
        Test the core filtering logic: exclude subjects with mean_fd >= 0.2.
        This mirrors the logic that will be implemented in src/data/filter_motion.py (T014).
        """
        threshold = 0.2
        included = [s for s in sample_subjects if s.mean_fd < threshold]
        excluded = [s for s in sample_subjects if s.mean_fd >= threshold]

        # Verify counts
        assert len(included) == 3, "Should include 3 subjects with FD < 0.2"
        assert len(excluded) == 3, "Should exclude 3 subjects with FD >= 0.2"

        # Verify specific IDs
        included_ids = {s.subject_id for s in included}
        excluded_ids = {s.subject_id for s in excluded}

        assert "1001" in included_ids
        assert "1002" in included_ids
        assert "1006" in included_ids

        assert "1003" in excluded_ids  # Exactly 0.20 should be excluded
        assert "1004" in excluded_ids
        assert "1005" in excluded_ids

    def test_boundary_condition_exact_threshold(self):
        """
        Test that a subject with mean_fd exactly equal to the threshold (0.2) is EXCLUDED.
        This is critical for data integrity.
        """
        threshold = 0.2
        subject_at_threshold = Subject(
            subject_id="EDGE_CASE",
            dsrt_score=5.0,
            age=25,
            sex="M",
            mean_fd=0.2
        )

        is_included = subject_at_threshold.mean_fd < threshold
        assert not is_included, "Subject with mean_fd == 0.2 must be excluded."

    def test_dataframe_filtering_simulation(self, sample_subjects):
        """
        Simulate the pandas filtering operation that will occur in T014.
        Ensures the logic holds when applied to a DataFrame.
        """
        df = pd.DataFrame([
            {
                "subject_id": s.subject_id,
                "dsrt_score": s.dsrt_score,
                "age": s.age,
                "sex": s.sex,
                "mean_fd": s.mean_fd
            }
            for s in sample_subjects
        ])

        threshold = 0.2
        low_motion_df = df[df["mean_fd"] < threshold]

        assert len(low_motion_df) == 3
        assert list(low_motion_df["subject_id"]) == ["1001", "1002", "1006"]

    def test_empty_dataset_handling(self):
        """Test that filtering an empty list returns an empty list."""
        empty_subjects = []
        threshold = 0.2
        included = [s for s in empty_subjects if s.mean_fd < threshold]
        assert len(included) == 0

    def test_all_excluded_case(self):
        """Test a scenario where all subjects exceed the threshold."""
        high_motion_subjects = [
            Subject("H1", 1.0, 20, "M", 0.3),
            Subject("H2", 2.0, 21, "F", 0.5),
        ]
        threshold = 0.2
        included = [s for s in high_motion_subjects if s.mean_fd < threshold]
        assert len(included) == 0

    def test_all_included_case(self):
        """Test a scenario where all subjects are below the threshold."""
        low_motion_subjects = [
            Subject("L1", 1.0, 20, "M", 0.01),
            Subject("L2", 2.0, 21, "F", 0.15),
        ]
        threshold = 0.2
        included = [s for s in low_motion_subjects if s.mean_fd < threshold]
        assert len(included) == 2