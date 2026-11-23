"""
Unit tests for the exclusion filter logic (T014a).

Tests verify that subjects with mean FD > 0.5 mm are correctly excluded
and that the pipeline does not crash when the cohort is small.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.exclusion_filter import filter_subjects_by_fd, FD_THRESHOLD


class TestExclusionFilter:
    """Test cases for filter_subjects_by_fd."""

    def test_filter_basic(self):
        """Test basic filtering with known values."""
        data = {
            "subject_id": ["S1", "S2", "S3", "S4", "S5"],
            "mean_fd": [0.1, 0.4, 0.5, 0.6, 0.9]
        }
        df = pd.DataFrame(data)

        filtered, excluded_count, original_count = filter_subjects_by_fd(df, "mean_fd", 0.5)

        assert original_count == 5
        assert excluded_count == 2
        assert len(filtered) == 3
        assert list(filtered["subject_id"]) == ["S1", "S2", "S3"]

    def test_filter_threshold_boundary(self):
        """Test that exactly 0.5 is included, >0.5 is excluded."""
        data = {
            "subject_id": ["S1", "S2"],
            "mean_fd": [0.5, 0.5001]
        }
        df = pd.DataFrame(data)

        filtered, excluded_count, _ = filter_subjects_by_fd(df, "mean_fd", 0.5)

        assert excluded_count == 1
        assert filtered.iloc[0]["subject_id"] == "S1"

    def test_filter_all_excluded(self):
        """Test behavior when all subjects are excluded."""
        data = {
            "subject_id": ["S1", "S2"],
            "mean_fd": [0.8, 0.9]
        }
        df = pd.DataFrame(data)

        filtered, excluded_count, original_count = filter_subjects_by_fd(df, "mean_fd", 0.5)

        assert len(filtered) == 0
        assert excluded_count == 2
        assert original_count == 2

    def test_filter_with_nan(self):
        """Test handling of NaN values (should be excluded)."""
        data = {
            "subject_id": ["S1", "S2", "S3"],
            "mean_fd": [0.1, np.nan, 0.6]
        }
        df = pd.DataFrame(data)

        filtered, excluded_count, _ = filter_subjects_by_fd(df, "mean_fd", 0.5)

        # S1 (0.1) kept. S2 (nan) excluded. S3 (0.6) excluded.
        assert len(filtered) == 1
        assert excluded_count == 2
        assert filtered.iloc[0]["subject_id"] == "S1"

    def test_filter_missing_column(self):
        """Test that missing column raises ValueError."""
        data = {
            "subject_id": ["S1"],
            "other_metric": [0.1]
        }
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="not found in DataFrame"):
            filter_subjects_by_fd(df, "mean_fd")

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=["subject_id", "mean_fd"])
        
        filtered, excluded_count, original_count = filter_subjects_by_fd(df, "mean_fd", 0.5)
        
        assert len(filtered) == 0
        assert excluded_count == 0
        assert original_count == 0
