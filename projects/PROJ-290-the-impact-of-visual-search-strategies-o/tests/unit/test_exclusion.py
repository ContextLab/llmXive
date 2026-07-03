import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

from code.data.exclusion import (
    calculate_missing_ratio,
    evaluate_participant_exclusion,
    run_exclusion_pipeline,
    MISSING_THRESHOLD
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
        assert ratio == 0.4  # 2 out of 5

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

    @pytest.fixture
    def sample_data(self):
        """Create sample participant data with varying missing ratios."""
        data = {
            'participant_id': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
            'gaze_x': [10.0, 11.0, np.nan, 20.0, 21.0, 22.0, np.nan, np.nan, np.nan, 40.0, 41.0, 42.0],
            'gaze_y': [100.0, 101.0, 102.0, 200.0, np.nan, 202.0, np.nan, np.nan, np.nan, 400.0, 401.0, 402.0]
        }
        return pd.DataFrame(data)

    def test_exclusion_threshold(self, sample_data):
        """Test that participants with >20% missing data are excluded."""
        filtered_df, stats = evaluate_participant_exclusion(
            df=sample_data,
            gaze_columns=['gaze_x', 'gaze_y'],
            participant_col='participant_id',
            threshold=0.20
        )

        # Participant 3 has 100% missing (6/6 values) -> excluded
        # Participant 1 has 1/6 missing (~16.7%) -> kept
        # Participant 2 has 1/6 missing (~16.7%) -> kept
        # Participant 4 has 0/6 missing (0%) -> kept

        assert stats['excluded_count'] == 1
        assert stats['excluded_participants'] == [3]
        assert stats['kept_count'] == 3
        assert stats['exclusion_rate'] == 1/4

        # Check filtered dataframe only contains kept participants
        assert 3 not in filtered_df['participant_id'].values
        assert 1 in filtered_df['participant_id'].values
        assert 2 in filtered_df['participant_id'].values
        assert 4 in filtered_df['participant_id'].values

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame(columns=['participant_id', 'gaze_x'])
        filtered_df, stats = evaluate_participant_exclusion(
            df=df,
            gaze_columns=['gaze_x'],
            participant_col='participant_id'
        )

        assert stats['total_participants'] == 0
        assert stats['excluded_count'] == 0
        assert stats['exclusion_rate'] == 0.0

    def test_custom_threshold(self, sample_data):
        """Test with custom threshold."""
        filtered_df, stats = evaluate_participant_exclusion(
            df=sample_data,
            gaze_columns=['gaze_x', 'gaze_y'],
            participant_col='participant_id',
            threshold=0.10  # Stricter threshold
        )

        # With 10% threshold, participants with 16.7% missing should be excluded
        assert stats['excluded_count'] == 3  # P1, P2, P3 all have >= 16.7%
        assert 4 in stats['kept_participants'] if 'kept_participants' in stats else True


class TestRunExclusionPipeline:
    """Tests for the full pipeline integration."""

    def test_pipeline_creates_files(self):
        """Test that pipeline creates output files."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            stats_path = Path(tmpdir) / "stats.json"

            # Create sample input
            data = {
                'participant_id': [1, 1, 2, 2],
                'gaze_x': [10.0, 11.0, np.nan, 22.0],
                'gaze_y': [100.0, 101.0, 200.0, 201.0]
            }
            pd.DataFrame(data).to_csv(input_path, index=False)

            # Run pipeline
            stats = run_exclusion_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                stats_path=str(stats_path)
            )

            # Verify files exist
            assert output_path.exists()
            assert stats_path.exists()

            # Verify stats content
            assert 'exclusion_rate' in stats
            assert 'excluded_count' in stats
            assert 'kept_count' in stats

            # Verify output file is valid CSV
            output_df = pd.read_csv(output_path)
            assert not output_df.empty

    def test_pipeline_handles_missing_input(self):
        """Test pipeline fails gracefully with missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            
            with pytest.raises(FileNotFoundError):
                run_exclusion_pipeline(input_path=str(input_path))