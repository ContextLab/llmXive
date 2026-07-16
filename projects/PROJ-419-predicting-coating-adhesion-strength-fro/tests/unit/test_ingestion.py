import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingestion import resolve_duplicates, exclude_missing_target_records, filter_astm_d4541_records

class TestResolveDuplicates:
    def test_resolve_duplicates_by_date(self):
        """Test that duplicates are resolved by keeping the most recent date."""
        data = {
            'sample_id': ['A', 'A', 'B'],
            'date': ['2023-01-01', '2023-01-05', '2023-01-01'],
            'value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        result = resolve_duplicates(df, date_col='date', sample_count_col='value')
        
        # Should keep the row with date 2023-01-05 for sample_id 'A'
        assert len(result) == 2
        assert result.loc[result['sample_id'] == 'A', 'date'].iloc[0] == pd.Timestamp('2023-01-05')
        assert result.loc[result['sample_id'] == 'A', 'value'].iloc[0] == 20

    def test_resolve_duplicates_by_sample_count(self):
        """Test that duplicates are resolved by keeping the highest sample count when date is missing."""
        data = {
            'sample_id': ['A', 'A', 'B'],
            'sample_count': [5, 10, 3],
            'value': [100, 200, 300]
        }
        df = pd.DataFrame(data)
        
        result = resolve_duplicates(df, date_col='nonexistent', sample_count_col='sample_count')
        
        # Should keep the row with sample_count 10 for sample_id 'A'
        assert len(result) == 2
        assert result.loc[result['sample_id'] == 'A', 'sample_count'].iloc[0] == 10
        assert result.loc[result['sample_id'] == 'A', 'value'].iloc[0] == 200

    def test_resolve_duplicates_empty_df(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['sample_id', 'date', 'value'])
        result = resolve_duplicates(df)
        assert result.empty

    def test_resolve_duplicates_no_duplicates(self):
        """Test that no changes occur if there are no duplicates."""
        data = {
            'sample_id': ['A', 'B', 'C'],
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        result = resolve_duplicates(df, date_col='date')
        assert len(result) == 3
        pd.testing.assert_frame_equal(result, df)

class TestExcludeMissingTargetRecords:
    def test_exclude_missing_target(self):
        """Test exclusion of records with missing target values."""
        data = {
            'id': [1, 2, 3, 4],
            'adhesion_strength': [10.0, np.nan, 15.0, np.nan]
        }
        df = pd.DataFrame(data)
        
        result = exclude_missing_target_records(df, target_col='adhesion_strength')
        
        assert len(result) == 2
        assert result['adhesion_strength'].isna().sum() == 0

    def test_exclude_missing_target_empty_df(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['id', 'adhesion_strength'])
        result = exclude_missing_target_records(df)
        assert result.empty

    def test_exclude_missing_target_no_missing(self):
        """Test that no rows are excluded if none are missing."""
        data = {
            'id': [1, 2, 3],
            'adhesion_strength': [10.0, 15.0, 20.0]
        }
        df = pd.DataFrame(data)
        result = exclude_missing_target_records(df)
        assert len(result) == 3

class TestFilterASTMD4541:
    def test_filter_astm_d4541(self):
        """Test filtering for ASTM D4541 records."""
        data = {
            'id': [1, 2, 3, 4],
            'test_standard': ['ASTM D4541', 'ISO 4624', 'ASTM D4541', 'Other']
        }
        df = pd.DataFrame(data)
        
        result = filter_astm_d4541_records(df)
        
        assert len(result) == 2
        assert all(result['test_standard'] == 'ASTM D4541')

    def test_filter_astm_d4541_no_match(self):
        """Test filtering when no records match."""
        data = {
            'id': [1, 2],
            'test_standard': ['ISO 4624', 'Other']
        }
        df = pd.DataFrame(data)
        result = filter_astm_d4541_records(df)
        assert result.empty

    def test_filter_astm_d4541_empty_df(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=['id', 'test_standard'])
        result = filter_astm_d4541_records(df)
        assert result.empty
