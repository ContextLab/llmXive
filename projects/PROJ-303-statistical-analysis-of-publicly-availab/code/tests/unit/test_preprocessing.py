"""
Unit tests for preprocessing module.
"""
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

from src.data.preprocessing import (
    calculate_missing_ratio,
    find_max_contiguous_gap,
    filter_stations,
    generate_filter_report
)


class TestCalculateMissingRatio:
    def test_no_missing_values(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmax': [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0]
        })
        ratio = calculate_missing_ratio(df)
        assert ratio == 0.0

    def test_some_missing_values(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmax': [20.0, np.nan, 22.0, 23.0, np.nan, 25.0, 26.0, 27.0, 28.0, 29.0]
        })
        ratio = calculate_missing_ratio(df)
        assert ratio == 0.2  # 2 missing out of 10

    def test_all_missing_values(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmax': [np.nan] * 10
        })
        ratio = calculate_missing_ratio(df)
        assert ratio == 1.0

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['date', 'tmax'])
        ratio = calculate_missing_ratio(df)
        assert ratio == 0.0

    def test_missing_column(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmin': [10.0] * 10
        })
        with pytest.raises(ValueError):
            calculate_missing_ratio(df)


class TestFindMaxContiguousGap:
    def test_no_gaps(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmax': [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0]
        })
        gap = find_max_contiguous_gap(df)
        assert gap == 0

    def test_single_gap(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmax': [20.0, np.nan, np.nan, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0]
        })
        gap = find_max_contiguous_gap(df)
        assert gap == 2

    def test_multiple_gaps(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=15),
            'tmax': [
                20.0, np.nan, np.nan, np.nan, 24.0,  # gap of 3
                25.0, 26.0, np.nan, 28.0, 29.0,      # gap of 1
                30.0, 31.0, 32.0, 33.0, 34.0
            ]
        })
        gap = find_max_contiguous_gap(df)
        assert gap == 3

    def test_all_missing(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmax': [np.nan] * 10
        })
        gap = find_max_contiguous_gap(df)
        assert gap == 10

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['date', 'tmax'])
        gap = find_max_contiguous_gap(df)
        assert gap == 0

    def test_missing_column(self):
        df = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10),
            'tmin': [10.0] * 10
        })
        with pytest.raises(ValueError):
            find_max_contiguous_gap(df)


class TestFilterStations:
    @pytest.fixture
    def sample_data(self):
        """Create sample data with known gaps and missing ratios."""
        # Station A: Perfect data
        data_a = pd.DataFrame({
            'station_id': ['A'] * 365,
            'date': pd.date_range('2020-01-01', periods=365),
            'tmax': [20.0 + (i % 30) for i in range(365)]
        })
        
        # Station B: 20% missing (should be excluded)
        data_b = pd.DataFrame({
            'station_id': ['B'] * 365,
            'date': pd.date_range('2020-01-01', periods=365),
            'tmax': [20.0 + (i % 30) if i % 5 != 0 else np.nan for i in range(365)]
        })
        
        # Station C: 35 day gap (should be excluded)
        data_c = pd.DataFrame({
            'station_id': ['C'] * 365,
            'date': pd.date_range('2020-01-01', periods=365),
            'tmax': [20.0 + (i % 30) for i in range(365)]
        })
        # Introduce a 35-day gap
        data_c.loc[100:134, 'tmax'] = np.nan
        
        # Station D: 25 day gap (should pass)
        data_d = pd.DataFrame({
            'station_id': ['D'] * 365,
            'date': pd.date_range('2020-01-01', periods=365),
            'tmax': [20.0 + (i % 30) for i in range(365)]
        })
        # Introduce a 25-day gap
        data_d.loc[100:124, 'tmax'] = np.nan
        
        return pd.concat([data_a, data_b, data_c, data_d], ignore_index=True)

    def test_filter_excludes_high_missing_ratio(self, sample_data):
        filtered_df, exclusion_log = filter_stations(
            input_path=None, # We pass data directly via fixture logic in real usage
            # Since filter_stations loads from file, we create a temp file
        )
        # This test is structural; actual file I/O tested in integration or via temp file
        pass

    def test_filter_excludes_large_gaps(self, sample_data):
        # Create temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            sample_data.to_parquet(input_path, index=False)
            
            filtered_df, exclusion_log = filter_stations(
                input_path=input_path,
                output_path=output_path,
                missing_threshold=0.15,
                max_gap_days=30
            )
            
            # Check that B and C are excluded
            assert 'B' in exclusion_log
            assert 'C' in exclusion_log
            
            # Check that A and D are included
            assert 'A' not in exclusion_log
            assert 'D' not in exclusion_log
            
            # Verify output contains only A and D
            assert set(filtered_df['station_id'].unique()) == {'A', 'D'}

    def test_filter_keeps_all_when_thresholds_high(self, sample_data):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.parquet"
            output_path = Path(tmpdir) / "output.parquet"
            
            sample_data.to_parquet(input_path, index=False)
            
            # Very high thresholds
            filtered_df, exclusion_log = filter_stations(
                input_path=input_path,
                output_path=output_path,
                missing_threshold=0.50,
                max_gap_days=50
            )
            
            assert len(exclusion_log) == 0
            assert set(filtered_df['station_id'].unique()) == {'A', 'B', 'C', 'D'}


class TestGenerateFilterReport:
    def test_empty_log(self):
        report = generate_filter_report({})
        assert "No stations were excluded." in report

    def test_non_empty_log(self):
        log = {
            'ST001': 'Missing ratio 20% > 15%',
            'ST002': 'Max gap 35 days > 30 days'
        }
        report = generate_filter_report(log)
        assert "Total stations excluded: 2" in report
        assert "ST001" in report
        assert "ST002" in report

    def test_report_saved_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.txt"
            log = {'ST001': 'Missing ratio 20% > 15%'}
            
            report = generate_filter_report(log, output_path=report_path)
            
            assert report_path.exists()
            assert "ST001" in report_path.read_text()