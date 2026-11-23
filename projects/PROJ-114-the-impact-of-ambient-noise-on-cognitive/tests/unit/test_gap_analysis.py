"""
Unit tests for gap analysis logic in data_ingestion.py (FR-007).

Tests:
- Binning noise logs into 1-minute intervals
- Calculation of valid_logging_proportion
- Exclusion of participants with <80% valid hours
- Detection and flagging of single continuous gaps >20% of total session time
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import analyze_gaps


class TestGapAnalysis:
    """Test suite for gap analysis logic."""

    def test_gap_analysis_valid_participant(self):
        """Test that a participant with >80% valid logging and no large gaps passes."""
        # Create noise logs with minimal gaps
        timestamps = pd.date_range('2024-01-01 09:00:00', periods=120, freq='30S')
        df = pd.DataFrame({
            'participant_id': ['P001'] * 120,
            'timestamp': timestamps,
            'db_level': np.random.uniform(40, 70, 120),
            'device_id': 'device_001'
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # P001 should not be excluded
        assert 'P001' not in excluded
        assert len(df_filtered) > 0
        assert 'P001' in df_filtered['participant_id'].values

    def test_gap_analysis_low_valid_proportion(self):
        """Test exclusion when valid_logging_proportion < 0.80."""
        # Create logs with only 50% coverage
        timestamps = pd.date_range('2024-01-01 09:00:00', periods=30, freq='1T')
        df = pd.DataFrame({
            'participant_id': ['P002'] * 30,
            'timestamp': timestamps,
            'db_level': np.random.uniform(40, 70, 30),
            'device_id': 'device_002'
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # P002 should be excluded due to low valid proportion
        assert 'P002' in excluded
        assert len(df_filtered[df_filtered['participant_id'] == 'P002']) == 0

    def test_gap_analysis_large_single_gap(self):
        """Test exclusion when a single continuous gap >20% of total session time."""
        # Create logs with a 30% gap in the middle
        # Total session: 100 minutes
        # Gap: 30 minutes (from minute 30 to minute 60)
        first_part = pd.date_range('2024-01-01 09:00:00', periods=30, freq='1T')
        second_part = pd.date_range('2024-01-01 10:00:00', periods=70, freq='1T')
        timestamps = list(first_part) + list(second_part)
        
        df = pd.DataFrame({
            'participant_id': ['P003'] * 100,
            'timestamp': timestamps,
            'db_level': np.random.uniform(40, 70, 100),
            'device_id': 'device_003'
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # P003 should be excluded due to large gap
        assert 'P003' in excluded
        assert len(df_filtered[df_filtered['participant_id'] == 'P003']) == 0

    def test_gap_analysis_multiple_participants(self):
        """Test gap analysis with multiple participants, mixed validity."""
        # P004: Valid (good coverage)
        valid_timestamps = pd.date_range('2024-01-01 09:00:00', periods=120, freq='30S')
        valid_df = pd.DataFrame({
            'participant_id': ['P004'] * 120,
            'timestamp': valid_timestamps,
            'db_level': np.random.uniform(40, 70, 120),
            'device_id': 'device_004'
        })
        
        # P005: Invalid (sparse coverage)
        sparse_timestamps = pd.date_range('2024-01-01 09:00:00', periods=20, freq='3T')
        sparse_df = pd.DataFrame({
            'participant_id': ['P005'] * 20,
            'timestamp': sparse_timestamps,
            'db_level': np.random.uniform(40, 70, 20),
            'device_id': 'device_005'
        })
        
        df = pd.concat([valid_df, sparse_df], ignore_index=True)
        df_filtered, excluded = analyze_gaps(df)
        
        # P004 should pass, P005 should be excluded
        assert 'P004' not in excluded
        assert 'P005' in excluded

    def test_gap_analysis_empty_dataframe(self):
        """Test handling of empty input."""
        df = pd.DataFrame(columns=['participant_id', 'timestamp', 'db_level', 'device_id'])
        
        df_filtered, excluded = analyze_gaps(df)
        
        assert df_filtered.empty
        assert len(excluded) == 0

    def test_gap_analysis_single_point(self):
        """Test handling of participant with single log entry."""
        df = pd.DataFrame({
            'participant_id': ['P006'],
            'timestamp': [datetime.now()],
            'db_level': [55.0],
            'device_id': ['device_006']
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # Single point should be treated as valid (100% coverage, 0% gap)
        assert 'P006' not in excluded
        assert len(df_filtered) == 1

    def test_gap_analysis_exactly_80_percent(self):
        """Test boundary condition: exactly 80% valid logging."""
        # Create 100 minutes of session, with 80 valid minutes and 20 gap
        valid_minutes = list(pd.date_range('2024-01-01 09:00:00', periods=80, freq='1T'))
        gap_start = valid_minutes[-1] + timedelta(minutes=1)
        gap_minutes = list(pd.date_range(gap_start, periods=20, freq='1T'))
        
        # Only log the valid minutes (no logs during gap)
        df = pd.DataFrame({
            'participant_id': ['P007'] * 80,
            'timestamp': valid_minutes,
            'db_level': np.random.uniform(40, 70, 80),
            'device_id': ['device_007'] * 80
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # At exactly 80%, should pass (>= 0.80)
        assert 'P007' not in excluded

    def test_gap_analysis_exactly_20_percent_gap(self):
        """Test boundary condition: exactly 20% max gap."""
        # Total 100 minutes, with exactly 20% gap
        first_part = list(pd.date_range('2024-01-01 09:00:00', periods=40, freq='1T'))
        gap_start = first_part[-1] + timedelta(minutes=1)
        second_part = list(pd.date_range(gap_start + timedelta(minutes=20), periods=40, freq='1T'))
        
        timestamps = first_part + second_part
        
        df = pd.DataFrame({
            'participant_id': ['P008'] * 80,
            'timestamp': timestamps,
            'db_level': np.random.uniform(40, 70, 80),
            'device_id': ['device_008'] * 80
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # At exactly 20% gap, should pass (<= 0.20)
        assert 'P008' not in excluded

    def test_gap_analysis_output_files(self, tmp_path):
        """Test that gap analysis generates expected output files."""
        # Temporarily change PROCESSED_DIR for this test
        from data_ingestion import PROCESSED_DIR as original_dir
        import data_ingestion
        
        data_ingestion.PROCESSED_DIR = tmp_path
        
        timestamps = pd.date_range('2024-01-01 09:00:00', periods=120, freq='30S')
        df = pd.DataFrame({
            'participant_id': ['P009'] * 120,
            'timestamp': timestamps,
            'db_level': np.random.uniform(40, 70, 120),
            'device_id': 'device_009'
        })
        
        df_filtered, excluded = analyze_gaps(df)
        
        # Check that gap_analysis_report.csv was created
        report_path = tmp_path / "gap_analysis_report.csv"
        assert report_path.exists()
        
        # Check that gap_exclusion_log.json was created
        exclusion_log_path = tmp_path / "gap_exclusion_log.json"
        assert exclusion_log_path.exists()
        
        # Restore original
        data_ingestion.PROCESSED_DIR = original_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])