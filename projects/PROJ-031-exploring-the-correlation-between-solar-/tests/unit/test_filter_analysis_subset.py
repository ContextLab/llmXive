"""
Unit tests for the analysis subset filtering logic (T016b).

Tests verify that:
1. Recurrent events are correctly filtered out
2. Non-recurrent events are preserved
3. The primary dataset remains unchanged (not tested here, but implied)
4. Error handling for missing files and columns works correctly
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from filter_analysis_subset import filter_non_recurrent_storms


class TestFilterAnalysisSubset:
    """Test suite for filter_non_recurrent_storms function."""

    def test_filter_removes_recurrent_events(self):
        """Verify that events with is_recurrent=True are removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "aligned_events.csv")
            output_path = os.path.join(tmpdir, "analysis_subset.csv")

            # Create test data with mixed recurrent flags
            test_data = {
                "event_id": [1, 2, 3, 4, 5],
                "timestamp": ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05"],
                "dst_min": [-50, -100, -30, -80, -120],
                "is_recurrent": [False, True, False, True, False]
            }
            df = pd.DataFrame(test_data)
            df.to_csv(input_path, index=False)

            # Run the filter
            count = filter_non_recurrent_storms(input_path, output_path)

            # Verify output
            result_df = pd.read_csv(output_path)
            assert len(result_df) == 3  # Only non-recurrent events
            assert count == 3
            assert all(result_df["is_recurrent"] == False)
            assert set(result_df["event_id"]) == {1, 3, 5}

    def test_filter_handles_missing_recurrent_flag(self):
        """Verify that rows with NaN/missing recurrent flag are kept."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "aligned_events.csv")
            output_path = os.path.join(tmpdir, "analysis_subset.csv")

            # Create test data with missing recurrent flags
            test_data = {
                "event_id": [1, 2, 3],
                "timestamp": ["2020-01-01", "2020-01-02", "2020-01-03"],
                "dst_min": [-50, -100, -30],
                "is_recurrent": [False, np.nan, True]
            }
            df = pd.DataFrame(test_data)
            df.to_csv(input_path, index=False)

            # Run the filter
            count = filter_non_recurrent_storms(input_path, output_path)

            # Verify output (NaN values should be kept as non-recurrent)
            result_df = pd.read_csv(output_path)
            assert len(result_df) == 2  # Event 1 (False) and Event 2 (NaN)
            assert count == 2
            assert set(result_df["event_id"]) == {1, 2}

    def test_filter_preserves_all_columns(self):
        """Verify that all columns from input are preserved in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "aligned_events.csv")
            output_path = os.path.join(tmpdir, "analysis_subset.csv")

            test_data = {
                "event_id": [1, 2, 3],
                "timestamp": ["2020-01-01", "2020-01-02", "2020-01-03"],
                "dst_min": [-50, -100, -30],
                "flare_flux": [1e-4, 2e-4, 3e-4],
                "cme_speed": [500, 800, 600],
                "is_recurrent": [False, True, False]
            }
            df = pd.DataFrame(test_data)
            df.to_csv(input_path, index=False)

            count = filter_non_recurrent_storms(input_path, output_path)
            result_df = pd.read_csv(output_path)

            assert list(result_df.columns) == list(df.columns)
            assert len(result_df) == 2

    def test_missing_input_file_raises_error(self):
        """Verify that missing input file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "nonexistent.csv")
            output_path = os.path.join(tmpdir, "output.csv")

            with pytest.raises(FileNotFoundError):
                filter_non_recurrent_storms(input_path, output_path)

    def test_missing_recurrent_column_raises_error(self):
        """Verify that missing recurrent column raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "aligned_events.csv")
            output_path = os.path.join(tmpdir, "analysis_subset.csv")

            # Create data without is_recurrent column
            test_data = {
                "event_id": [1, 2, 3],
                "timestamp": ["2020-01-01", "2020-01-02", "2020-01-03"],
                "dst_min": [-50, -100, -30]
            }
            df = pd.DataFrame(test_data)
            df.to_csv(input_path, index=False)

            with pytest.raises(ValueError, match="Required column 'is_recurrent' not found"):
                filter_non_recurrent_storms(input_path, output_path)

    def test_empty_result_when_all_recurrent(self):
        """Verify that output is empty (but valid) if all events are recurrent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "aligned_events.csv")
            output_path = os.path.join(tmpdir, "analysis_subset.csv")

            test_data = {
                "event_id": [1, 2, 3],
                "timestamp": ["2020-01-01", "2020-01-02", "2020-01-03"],
                "dst_min": [-50, -100, -30],
                "is_recurrent": [True, True, True]
            }
            df = pd.DataFrame(test_data)
            df.to_csv(input_path, index=False)

            count = filter_non_recurrent_storms(input_path, output_path)
            result_df = pd.read_csv(output_path)

            assert count == 0
            assert len(result_df) == 0
            # Verify file exists and has headers
            assert os.path.exists(output_path)
            assert list(result_df.columns) == list(df.columns)