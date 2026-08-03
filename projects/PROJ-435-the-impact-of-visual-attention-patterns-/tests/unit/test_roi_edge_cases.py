"""
Unit tests for ROI edge case handling (T016).

Tests verify that:
1. Trials with missing ROI coordinates are excluded
2. Exclusion counts are logged correctly
3. Zero fixations on source ROI are treated as valid data (T017)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.roi_edge_cases import (
    is_roi_coordinate_valid,
    exclude_trials_with_missing_roi,
    handle_zero_fixation_roi,
    aggregate_exclusion_stats
)


class TestROICoordinateValidation:
    """Test ROI coordinate validation logic."""
    
    def test_valid_coordinates(self):
        """Test that valid ROI coordinates return True."""
        row = pd.Series({
            'roi_x1': 10.0,
            'roi_y1': 20.0,
            'roi_x2': 100.0,
            'roi_y2': 200.0
        })
        roi_columns = ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2']
        
        assert is_roi_coordinate_valid(row, roi_columns) is True
    
    def test_missing_column(self):
        """Test that missing ROI column returns False."""
        row = pd.Series({
            'roi_x1': 10.0,
            'roi_y1': 20.0,
            'roi_x2': 100.0
            # roi_y2 is missing
        })
        roi_columns = ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2']
        
        assert is_roi_coordinate_valid(row, roi_columns) is False
    
    def test_nan_coordinates(self):
        """Test that NaN coordinates return False."""
        row = pd.Series({
            'roi_x1': 10.0,
            'roi_y1': np.nan,
            'roi_x2': 100.0,
            'roi_y2': 200.0
        })
        roi_columns = ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2']
        
        assert is_roi_coordinate_valid(row, roi_columns) is False
    
    def test_none_coordinates(self):
        """Test that None coordinates return False."""
        row = pd.Series({
            'roi_x1': 10.0,
            'roi_y1': None,
            'roi_x2': 100.0,
            'roi_y2': 200.0
        })
        roi_columns = ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2']
        
        assert is_roi_coordinate_valid(row, roi_columns) is False
    
    def test_empty_string_coordinates(self):
        """Test that empty string coordinates return False."""
        row = pd.Series({
            'roi_x1': 10.0,
            'roi_y1': '',
            'roi_x2': 100.0,
            'roi_y2': 200.0
        })
        roi_columns = ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2']
        
        assert is_roi_coordinate_valid(row, roi_columns) is False


class TestExcludeTrialsWithMissingROI:
    """Test trial exclusion logic for missing ROI coordinates."""
    
    def test_no_missing_coordinates(self):
        """Test that no trials are excluded when all coordinates are valid."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3],
            'participant_id': ['P1', 'P2', 'P3'],
            'roi_x1': [10.0, 20.0, 30.0],
            'roi_y1': [10.0, 20.0, 30.0],
            'roi_x2': [100.0, 100.0, 100.0],
            'roi_y2': [100.0, 100.0, 100.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exclusion_log = Path(tmpdir) / 'exclusions.json'
            filtered_df, excluded_count, exclusion_records = exclude_trials_with_missing_roi(
                df, 
                ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2'],
                exclusion_log
            )
        
        assert excluded_count == 0
        assert len(filtered_df) == 3
        assert len(exclusion_records) == 0
    
    def test_some_missing_coordinates(self):
        """Test that trials with missing coordinates are excluded."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3, 4],
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'roi_x1': [10.0, np.nan, 30.0, 40.0],
            'roi_y1': [10.0, 20.0, 30.0, 40.0],
            'roi_x2': [100.0, 100.0, np.nan, 100.0],
            'roi_y2': [100.0, 100.0, 100.0, 100.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exclusion_log = Path(tmpdir) / 'exclusions.json'
            filtered_df, excluded_count, exclusion_records = exclude_trials_with_missing_roi(
                df, 
                ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2'],
                exclusion_log
            )
        
        # Trials 2 and 3 should be excluded
        assert excluded_count == 2
        assert len(filtered_df) == 2
        assert len(exclusion_records) == 2
        
        # Check that excluded trials are correctly identified
        excluded_trial_ids = [r['trial_id'] for r in exclusion_records]
        assert 2 in excluded_trial_ids
        assert 3 in excluded_trial_ids
    
    def test_all_missing_coordinates(self):
        """Test that all trials are excluded when all have missing coordinates."""
        df = pd.DataFrame({
            'trial_id': [1, 2],
            'participant_id': ['P1', 'P2'],
            'roi_x1': [np.nan, np.nan],
            'roi_y1': [np.nan, np.nan],
            'roi_x2': [np.nan, np.nan],
            'roi_y2': [np.nan, np.nan]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exclusion_log = Path(tmpdir) / 'exclusions.json'
            filtered_df, excluded_count, exclusion_records = exclude_trials_with_missing_roi(
                df, 
                ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2'],
                exclusion_log
            )
        
        assert excluded_count == 2
        assert len(filtered_df) == 0
        assert len(exclusion_records) == 2
    
    def test_exclusion_log_written(self):
        """Test that exclusion log is written to file."""
        df = pd.DataFrame({
            'trial_id': [1, 2],
            'participant_id': ['P1', 'P2'],
            'roi_x1': [10.0, np.nan],
            'roi_y1': [10.0, 20.0],
            'roi_x2': [100.0, 100.0],
            'roi_y2': [100.0, 100.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exclusion_log = Path(tmpdir) / 'exclusions.json'
            filtered_df, excluded_count, exclusion_records = exclude_trials_with_missing_roi(
                df, 
                ['roi_x1', 'roi_y1', 'roi_x2', 'roi_y2'],
                exclusion_log
            )
            
            # Check that log file exists and contains data
            assert exclusion_log.exists()
            with open(exclusion_log, 'r') as f:
                log_data = json.load(f)
            assert len(log_data) == 1
            assert log_data[0]['reason'] == 'missing_roi_coordinates'


class TestZeroFixationROI:
    """Test handling of zero fixations on source ROI (T017)."""
    
    def test_zero_fixations_marked(self):
        """Test that zero fixations on source ROI are marked as valid."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3],
            'roi_type': ['source_attribution', 'source_attribution', 'other'],
            'duration': [0.0, 0.0, 50.0]
        })
        
        filtered_df, zero_count = handle_zero_fixation_roi(df)
        
        assert zero_count == 2
        assert filtered_df.loc[0, 'zero_fixation_source_roi'] is True
        assert filtered_df.loc[1, 'zero_fixation_source_roi'] is True
        assert filtered_df.loc[2, 'zero_fixation_source_roi'] is False
    
    def test_non_zero_fixations_not_marked(self):
        """Test that non-zero fixations are not marked."""
        df = pd.DataFrame({
            'trial_id': [1, 2],
            'roi_type': ['source_attribution', 'source_attribution'],
            'duration': [100.0, 200.0]
        })
        
        filtered_df, zero_count = handle_zero_fixation_roi(df)
        
        assert zero_count == 0
        assert filtered_df.loc[0, 'zero_fixation_source_roi'] is False
        assert filtered_df.loc[1, 'zero_fixation_source_roi'] is False
    
    def test_missing_roi_type_column(self):
        """Test handling when ROI type column is missing."""
        df = pd.DataFrame({
            'trial_id': [1, 2],
            'duration': [100.0, 200.0]
        })
        
        filtered_df, zero_count = handle_zero_fixation_roi(df)
        
        assert zero_count == 0
        # Should not crash, just return original df


class TestAggregateExclusionStats:
    """Test aggregation of exclusion statistics."""
    
    def test_no_exclusions(self):
        """Test stats when no exclusions occurred."""
        stats = aggregate_exclusion_stats([], 100)
        
        assert stats['total_trials'] == 100
        assert stats['excluded_trials'] == 0
        assert stats['retained_trials'] == 100
        assert stats['exclusion_rate'] == 0.0
        assert stats['reasons'] == {}
    
    def test_with_exclusions(self):
        """Test stats with multiple exclusions."""
        exclusion_records = [
            {'trial_id': 1, 'reason': 'missing_roi_coordinates'},
            {'trial_id': 2, 'reason': 'missing_roi_coordinates'},
            {'trial_id': 3, 'reason': 'missing_roi_coordinates'}
        ]
        
        stats = aggregate_exclusion_stats(exclusion_records, 100)
        
        assert stats['total_trials'] == 100
        assert stats['excluded_trials'] == 3
        assert stats['retained_trials'] == 97
        assert stats['exclusion_rate'] == 0.03
        assert stats['reasons'] == {'missing_roi_coordinates': 3}
    
    def test_multiple_reasons(self):
        """Test stats with multiple exclusion reasons."""
        exclusion_records = [
            {'trial_id': 1, 'reason': 'missing_roi_coordinates'},
            {'trial_id': 2, 'reason': 'missing_roi_coordinates'},
            {'trial_id': 3, 'reason': 'invalid_participant'}
        ]
        
        stats = aggregate_exclusion_stats(exclusion_records, 100)
        
        assert stats['reasons'] == {
            'missing_roi_coordinates': 2,
            'invalid_participant': 1
        }
    
    def test_stats_written_to_file(self):
        """Test that stats are written to file when path provided."""
        exclusion_records = [
            {'trial_id': 1, 'reason': 'missing_roi_coordinates'}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            stats_path = Path(tmpdir) / 'stats.json'
            stats = aggregate_exclusion_stats(exclusion_records, 100, stats_path)
            
            assert stats_path.exists()
            with open(stats_path, 'r') as f:
                file_stats = json.load(f)
            assert file_stats == stats