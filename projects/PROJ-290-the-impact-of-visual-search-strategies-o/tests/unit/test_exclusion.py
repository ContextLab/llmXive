"""
Unit tests for participant exclusion logic (T014).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.exclusion import (
    calculate_missing_ratio,
    evaluate_participant_exclusion,
    run_exclusion_pipeline
)


class TestCalculateMissingRatio:
    """Tests for calculate_missing_ratio function."""

    def test_no_missing_data(self):
        """Test with complete data."""
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        ratio = calculate_missing_ratio(data)
        assert ratio == 0.0

    def test_all_missing_data(self):
        """Test with all missing data."""
        data = pd.Series([np.nan, np.nan, np.nan])
        ratio = calculate_missing_ratio(data)
        assert ratio == 1.0

    def test_partial_missing_data(self):
        """Test with partial missing data."""
        data = pd.Series([1.0, np.nan, 3.0, np.nan, 5.0])
        ratio = calculate_missing_ratio(data)
        assert ratio == 0.4  # 2 out of 5 missing

    def test_empty_series(self):
        """Test with empty series."""
        data = pd.Series([], dtype=float)
        ratio = calculate_missing_ratio(data)
        assert ratio == 1.0

    def test_none_input(self):
        """Test with None input."""
        ratio = calculate_missing_ratio(None)
        assert ratio == 1.0


class TestEvaluateParticipantExclusion:
    """Tests for evaluate_participant_exclusion function."""

    def test_below_threshold(self):
        """Test participant below exclusion threshold."""
        data = pd.DataFrame({
            "participant_id": ["p1"],
            "gaze_coordinates": [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        should_exclude, ratio, details = evaluate_participant_exclusion(
            data, threshold=0.20
        )
        assert should_exclude is False
        assert ratio == 0.0
        assert details["excluded"] is False

    def test_above_threshold(self):
        """Test participant above exclusion threshold."""
        # 3 out of 5 missing = 60% > 20%
        data = pd.DataFrame({
            "participant_id": ["p1"],
            "gaze_coordinates": [1.0, np.nan, np.nan, 4.0, np.nan]
        })
        should_exclude, ratio, details = evaluate_participant_exclusion(
            data, threshold=0.20
        )
        assert should_exclude is True
        assert ratio == 0.6
        assert details["excluded"] is True

    def test_missing_column(self):
        """Test when required column is missing."""
        data = pd.DataFrame({
            "participant_id": ["p1"],
            "other_column": [1.0, 2.0, 3.0]
        })
        should_exclude, ratio, details = evaluate_participant_exclusion(
            data, threshold=0.20, gaze_column="gaze_coordinates"
        )
        assert should_exclude is True
        assert ratio == 1.0
        assert "Missing required column" in details["reason"]

    def test_custom_threshold(self):
        """Test with custom threshold."""
        # 40% missing
        data = pd.DataFrame({
            "participant_id": ["p1"],
            "gaze_coordinates": [1.0, np.nan, np.nan, np.nan, 5.0]
        })
        # With 0.50 threshold, should NOT exclude
        should_exclude, ratio, details = evaluate_participant_exclusion(
            data, threshold=0.50
        )
        assert should_exclude is False
        assert ratio == 0.4

        # With 0.30 threshold, should exclude
        should_exclude, ratio, details = evaluate_participant_exclusion(
            data, threshold=0.30
        )
        assert should_exclude is True


class TestRunExclusionPipeline:
    """Tests for run_exclusion_pipeline function."""

    def test_pipeline_creates_output(self, tmp_path):
        """Test that pipeline creates cleaned output file."""
        # Create test data
        test_data = pd.DataFrame({
            "participant_id": ["p1", "p1", "p1", "p2", "p2", "p2"],
            "gaze_coordinates": [1.0, 2.0, 3.0, np.nan, np.nan, np.nan],
            "trial_data": [10, 20, 30, 40, 50, 60]
        })

        input_file = tmp_path / "features.csv"
        output_file = tmp_path / "features_cleaned.csv"
        report_file = tmp_path / "exclusion_report.json"

        test_data.to_csv(input_file, index=False)

        # Run pipeline
        report = run_exclusion_pipeline(
            input_path=str(input_file),
            output_path=str(output_file),
            threshold=0.20,
            gaze_column="gaze_coordinates"
        )

        # Verify output file created
        assert output_file.exists()
        assert report_file.exists()

        # Verify exclusion logic
        assert report["excluded_count"] == 1
        assert report["included_count"] == 1
        assert report["exclusion_rate"] == 0.5

        # Verify cleaned data
        cleaned_df = pd.read_csv(output_file)
        assert len(cleaned_df) == 3  # Only p1's records
        assert all(cleaned_df["participant_id"] == "p1")

    def test_pipeline_no_included_participants(self, tmp_path):
        """Test pipeline when all participants are excluded."""
        # Create test data where all participants have >20% missing
        test_data = pd.DataFrame({
            "participant_id": ["p1", "p1", "p2", "p2"],
            "gaze_coordinates": [np.nan, np.nan, np.nan, np.nan],
            "trial_data": [10, 20, 30, 40]
        })

        input_file = tmp_path / "features.csv"
        output_file = tmp_path / "features_cleaned.csv"

        test_data.to_csv(input_file, index=False)

        # Run pipeline
        report = run_exclusion_pipeline(
            input_path=str(input_file),
            output_path=str(output_file),
            threshold=0.20,
            gaze_column="gaze_coordinates"
        )

        # Verify exclusion
        assert report["excluded_count"] == 2
        assert report["included_count"] == 0
        assert report["exclusion_rate"] == 1.0

        # Output file should not be created when no participants remain
        assert not output_file.exists()

    def test_pipeline_logging_exclusion_rate(self, tmp_path, caplog):
        """Test that exclusion rate is logged."""
        import logging

        test_data = pd.DataFrame({
            "participant_id": ["p1", "p1", "p1", "p2", "p2", "p2"],
            "gaze_coordinates": [1.0, 2.0, 3.0, np.nan, np.nan, np.nan],
            "trial_data": [10, 20, 30, 40, 50, 60]
        })

        input_file = tmp_path / "features.csv"
        output_file = tmp_path / "features_cleaned.csv"

        test_data.to_csv(input_file, index=False)

        with caplog.at_level(logging.INFO):
            run_exclusion_pipeline(
                input_path=str(input_file),
                output_path=str(output_file),
                threshold=0.20,
                gaze_column="gaze_coordinates"
            )

        # Check that exclusion rate is logged
        log_output = " ".join(caplog.messages)
        assert "EXCLUSION SUMMARY" in log_output
        assert "Excluded:" in log_output
        assert "0.50" in log_output or "50%" in log_output