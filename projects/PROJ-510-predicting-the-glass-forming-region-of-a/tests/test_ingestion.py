"""
Integration tests for data ingestion pipeline (User Story 1).
Tests for T012, T013, T017.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from ingestion import (
    load_glass_data,
    filter_ternary_alloys,
    validate_critical_cooling_rate,
    MIN_ROWS
)

class TestIngestion:
    """Tests for data loading and filtering."""

    @patch('ingestion.load_dataset')
    def test_load_glass_data_success(self, mock_load_dataset):
        """Test successful loading of the glass dataset."""
        # Mock the dataset
        mock_data = MagicMock()
        mock_data.to_pandas.return_value = pd.DataFrame({
            'composition': ['Fe:0.5,Cr:0.3,Ni:0.2'],
            'critical_cooling_rate': [100.0]
        })
        mock_load_dataset.return_value = mock_data

        df = load_glass_data()
        
        mock_load_dataset.assert_called_once_with("matsci/glass-forming-ability")
        assert isinstance(df, pd.DataFrame)
        assert 'composition' in df.columns
        assert 'critical_cooling_rate' in df.columns

    @patch('ingestion.load_dataset')
    def test_filter_ternary_alloys(self, mock_load_dataset):
        """Test filtering for ternary alloys only."""
        # Mock data with mixed alloy types
        mock_data = MagicMock()
        mock_data.to_pandas.return_value = pd.DataFrame({
            'composition': [
                'Fe:0.5,Cr:0.3,Ni:0.2', # Ternary
                'Fe:0.4,Cr:0.3,Ni:0.2,Cu:0.1', # Quaternary
                'Fe:0.6,Cr:0.4', # Binary
                'Fe:0.3,Cr:0.3,Ni:0.3,Mo:0.1' # Quaternary
            ],
            'critical_cooling_rate': [100.0, 200.0, 300.0, 400.0]
        })
        mock_load_dataset.return_value = mock_data

        df = load_glass_data()
        filtered_df = filter_ternary_alloys(df)

        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['composition'] == 'Fe:0.5,Cr:0.3,Ni:0.2'

    def test_validate_critical_cooling_rate_count(self):
        """Test validation fails if count < 500."""
        # Create exactly 499 rows
        data = {
            'critical_cooling_rate': [10.0] * 499
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        assert "entries" in str(exc_info.value).lower()
        assert str(MIN_ROWS) in str(exc_info.value)

    def test_validate_critical_cooling_rate_variance(self):
        """Test validation fails if variance is zero."""
        # Create 1000 rows with same value (zero variance)
        data = {
            'critical_cooling_rate': [10.0] * 1000
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        assert "variance" in str(exc_info.value).lower()

    def test_validate_critical_cooling_rate_nan(self):
        """Test validation fails if variance is NaN."""
        # Create 1000 rows with all NaN
        data = {
            'critical_cooling_rate': [np.nan] * 1000
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            validate_critical_cooling_rate(df)

    def test_validate_critical_cooling_rate_missing_column(self):
        """Test validation fails if the column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        with pytest.raises(ValueError) as exc_info:
            validate_critical_cooling_rate(df)
        assert "not found" in str(exc_info.value).lower()

    def test_integration_pipeline_row_count(self):
        """
        Integration test: Ensure that if the ingestion pipeline runs successfully,
        it produces at least MIN_ROWS (500) valid records.
        This test mocks the real data source to simulate a successful fetch
        and verifies the downstream filtering and validation logic.
        """
        # Simulate a dataset with enough rows to pass filtering
        # We create 600 rows: 550 ternary, 50 quaternary (to be filtered out)
        compositions = []
        ccr_values = []
        
        for i in range(550):
            # Ternary alloy
            compositions.append(f"Fe:{0.5+i*0.0001},Cr:{0.3-i*0.0001},Ni:0.2")
            ccr_values.append(100.0 + i)
        
        for i in range(50):
            # Quaternary alloy (should be filtered)
            compositions.append(f"Fe:0.4,Cr:0.3,Ni:0.2,Cu:0.1")
            ccr_values.append(200.0)

        mock_data = MagicMock()
        mock_data.to_pandas.return_value = pd.DataFrame({
            'composition': compositions,
            'critical_cooling_rate': ccr_values
        })

        with patch('ingestion.load_dataset', return_value=mock_data):
            # Run the pipeline logic
            raw_df = load_glass_data()
            filtered_df = filter_ternary_alloys(raw_df)
            
            # Verify we have at least MIN_ROWS
            assert len(filtered_df) >= MIN_ROWS, f"Expected >= {MIN_ROWS} rows, got {len(filtered_df)}"
            
            # Verify no NaN in target column
            assert not filtered_df['critical_cooling_rate'].isna().any(), "Found NaN in critical_cooling_rate"
            
            # Verify validation passes
            try:
                validate_critical_cooling_rate(filtered_df)
            except ValueError:
                pytest.fail("Validation failed unexpectedly on valid data")

if __name__ == '__main__':
    pytest.main([__file__, "-v"])