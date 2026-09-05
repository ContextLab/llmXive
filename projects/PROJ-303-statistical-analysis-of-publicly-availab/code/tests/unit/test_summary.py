"""
Unit tests for the summary statistics reporter.
"""

import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.summary import (
    load_extreme_events,
    calculate_station_statistics,
    calculate_overall_statistics,
    generate_sensitivity_report,
    generate_summary_report,
    main
)


@pytest.fixture
def sample_extreme_events_df():
    """Create a sample DataFrame for testing."""
    data = {
        'station_id': ['STA001', 'STA001', 'STA001', 'STA002', 'STA002', 'STA003'],
        'date': pd.to_datetime([
            '2010-01-01', '2010-06-15', '2010-12-31',
            '2010-03-20', '2010-09-10',
            '2010-07-04'
        ]),
        'magnitude': [35.5, 42.0, 38.2, 36.0, 40.5, 39.8],
        'threshold_value': [35.0, 35.0, 35.0, 36.0, 36.0, 37.5]
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_df():
    """Create an empty DataFrame for testing edge cases."""
    return pd.DataFrame(columns=['station_id', 'date', 'magnitude', 'threshold_value'])


class TestCalculateStationStatistics:
    def test_calculate_statistics(self, sample_extreme_events_df):
        """Test that station statistics are calculated correctly."""
        stats = calculate_station_statistics(sample_extreme_events_df)

        assert len(stats) == 3  # 3 unique stations
        assert 'station_id' in stats.columns
        assert 'exceedance_count' in stats.columns
        assert 'avg_magnitude' in stats.columns

        # Check STA001 stats
        sta001 = stats[stats['station_id'] == 'STA001'].iloc[0]
        assert sta001['exceedance_count'] == 3
        assert abs(sta001['avg_magnitude'] - 38.56666666666667) < 0.001

    def test_empty_dataframe(self, empty_df):
        """Test handling of empty DataFrame."""
        stats = calculate_station_statistics(empty_df)
        assert stats.empty


class TestCalculateOverallStatistics:
    def test_overall_stats(self, sample_extreme_events_df):
        """Test overall statistics calculation."""
        stats = calculate_overall_statistics(sample_extreme_events_df)

        assert stats['total_stations'] == 3
        assert stats['total_exceedances'] == 6
        assert abs(stats['global_avg_magnitude'] - 38.666666666666664) < 0.001
        assert stats['global_max_magnitude'] == 42.0
        assert stats['global_min_magnitude'] == 35.5

    def test_empty_dataframe(self, empty_df):
        """Test handling of empty DataFrame."""
        stats = calculate_overall_statistics(empty_df)
        assert stats['total_stations'] == 0
        assert stats['total_exceedances'] == 0
        assert stats['global_avg_magnitude'] is None


class TestGenerateSensitivityReport:
    def test_sensitivity_report(self, sample_extreme_events_df):
        """Test sensitivity report generation."""
        report = generate_sensitivity_report(sample_extreme_events_df, [90, 95])

        assert 'analysis_type' in report
        assert report['analysis_type'] == 'sensitivity'
        assert len(report['results']) == 2

        # Check first result
        first_result = report['results'][0]
        assert 'percentile' in first_result
        assert 'exceedance_count' in first_result

    def test_empty_dataframe(self, empty_df):
        """Test sensitivity report with empty DataFrame."""
        report = generate_sensitivity_report(empty_df)
        assert 'note' in report
        assert 'No data available' in report['note']


class TestGenerateSummaryReport:
    def test_full_report(self, sample_extreme_events_df):
        """Test full summary report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary_report.json"
            report = generate_summary_report(sample_extreme_events_df, str(output_path))

            assert 'overall_statistics' in report
            assert 'station_statistics' in report
            assert 'sensitivity_report' in report
            assert report['overall_statistics']['total_stations'] == 3

            # Check file was written
            assert output_path.exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded['overall_statistics']['total_stations'] == 3

    def test_report_without_sensitivity(self, sample_extreme_events_df):
        """Test report generation without sensitivity analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary_report.json"
            report = generate_summary_report(
                sample_extreme_events_df,
                str(output_path),
                include_sensitivity=False
            )

            assert 'sensitivity_report' not in report


class TestLoadExtremeEvents:
    def test_load_parquet(self, sample_extreme_events_df):
        """Test loading from parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test_events.parquet"
            sample_extreme_events_df.to_parquet(parquet_path)

            loaded_df = load_extreme_events(str(parquet_path))

            assert len(loaded_df) == len(sample_extreme_events_df)
            assert list(loaded_df.columns) == list(sample_extreme_events_df.columns)

    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_extreme_events("/nonexistent/path/file.parquet")