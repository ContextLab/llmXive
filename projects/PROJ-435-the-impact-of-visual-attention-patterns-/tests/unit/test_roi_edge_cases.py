import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.roi_edge_cases import handle_zero_fixation_roi, exclude_trials_with_missing_roi, is_roi_coordinate_valid

class TestHandleZeroFixationROI:
    """Test T017: Handle edge cases: treat zero fixations on source ROI as valid data."""

    def test_zero_fixations_explicitly_recorded(self):
        """
        Test that if a participant/headline combination has no fixations on the source ROI,
        a row is inserted with duration=0 instead of being missing.
        """
        # Setup: Data where P1-H1 has source_attribution, but P2-H1 does NOT
        data = {
            "participant_id": [1, 1, 2],
            "headline_id": [101, 101, 101],
            "roi_type": ["source_attribution", "headline_text", "headline_text"],
            "fixation_duration": [150.0, 200.0, 100.0]
        }
        df = pd.DataFrame(data)

        # Execute
        result = handle_zero_fixation_roi(df, target_roi="source_attribution")

        # Assert: P2-H1-source_attribution must exist with duration 0
        missing_row = result[
            (result["participant_id"] == 2) &
            (result["headline_id"] == 101) &
            (result["roi_type"] == "source_attribution")
        ]

        assert not missing_row.empty, "Row for zero fixations was not created."
        assert missing_row["fixation_duration"].iloc[0] == 0.0, "Duration should be 0, not missing."

    def test_existing_fixations_preserved(self):
        """Ensure that existing fixations are not overwritten or removed."""
        data = {
            "participant_id": [1],
            "headline_id": [101],
            "roi_type": ["source_attribution"],
            "fixation_duration": [250.5]
        }
        df = pd.DataFrame(data)

        result = handle_zero_fixation_roi(df, target_roi="source_attribution")

        # Check that the original value is preserved
        original_row = result[
            (result["participant_id"] == 1) &
            (result["headline_id"] == 101) &
            (result["roi_type"] == "source_attribution")
        ]
        assert not original_row.empty
        assert original_row["fixation_duration"].iloc[0] == 250.5

    def test_multiple_headlines_and_participants(self):
        """Test logic with multiple participants and headlines."""
        data = {
            "participant_id": [1, 1, 2, 3],
            "headline_id": [101, 102, 101, 101],
            "roi_type": ["source_attribution", "headline_text", "headline_text", "source_attribution"],
            "fixation_duration": [100.0, 50.0, 60.0, 200.0]
        }
        df = pd.DataFrame(data)

        result = handle_zero_fixation_roi(df, target_roi="source_attribution")

        # P1-H1: Has source (100) -> OK
        # P1-H2: No source -> Should be added (0)
        # P2-H1: No source -> Should be added (0)
        # P3-H1: Has source (200) -> OK

        # Check P1-H2
        p1_h2 = result[
            (result["participant_id"] == 1) &
            (result["headline_id"] == 102) &
            (result["roi_type"] == "source_attribution")
        ]
        assert not p1_h2.empty
        assert p1_h2["fixation_duration"].iloc[0] == 0.0

        # Check P2-H1
        p2_h1 = result[
            (result["participant_id"] == 2) &
            (result["headline_id"] == 101) &
            (result["roi_type"] == "source_attribution")
        ]
        assert not p2_h1.empty
        assert p2_h1["fixation_duration"].iloc[0] == 0.0

class TestExcludeTrialsMissingROI:
    """Test T016: Exclude trials with missing ROI coordinates."""

    def test_exclude_missing_coordinates(self):
        """Verify that trials with None/missing ROI coordinates are excluded."""
        data = {
            "trial_id": [1, 2, 3],
            "source_attribution_roi": [
                {"x_min": 10, "x_max": 20, "y_min": 10, "y_max": 20}, # Valid
                None,                                                  # Invalid
                {"x_min": 10, "x_max": 20, "y_min": 10}               # Invalid (missing y_max)
            ],
            "value": [100, 200, 300]
        }
        df = pd.DataFrame(data)

        filtered_df, count = exclude_trials_with_missing_roi(df, roi_col="source_attribution_roi")

        assert count == 2, "Should exclude 2 invalid trials."
        assert len(filtered_df) == 1, "Should keep 1 valid trial."
        assert filtered_df.iloc[0]["trial_id"] == 1

    def test_is_roi_coordinate_valid(self):
        """Unit test for the coordinate validation helper."""
        assert is_roi_coordinate_valid({"x_min": 0, "x_max": 10, "y_min": 0, "y_max": 10})
        assert not is_roi_coordinate_valid(None)
        assert not is_roi_coordinate_valid({"x_min": 0, "x_max": 10}) # Missing Y
        assert not is_roi_coordinate_valid({"x_min": 0, "x_max": 10, "y_min": 0, "y_max": None})