"""
Unit tests for climate data acquisition (T009).

Tests:
- Schema validation for climate data
- Data merging logic
- Output file generation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_acquisition_climate import merge_climate_data

class TestClimateDataMerging:
    """Test cases for merging climate data."""
    
    def test_merge_precip_and_temp(self):
        """Test merging precipitation and temperature data."""
        precip_df = pd.DataFrame({
            'site_id': ['site1', 'site1', 'site2', 'site2'],
            'date': pd.to_datetime(['2020-01-01', '2020-02-01', '2020-01-01', '2020-02-01']),
            'precip_mm': [10.5, 15.2, 8.0, 12.3]
        })
        
        temp_df = pd.DataFrame({
            'site_id': ['site1', 'site1', 'site2', 'site2'],
            'date': pd.to_datetime(['2020-01-01', '2020-02-01', '2020-01-01', '2020-02-01']),
            'temp_avg_c': [25.0, 26.5, 20.0, 21.0]
        })
        
        merged = merge_climate_data(precip_df, temp_df)
        
        assert len(merged) == 4
        assert 'precip_mm' in merged.columns
        assert 'temp_avg_c' in merged.columns
        assert all(merged['site_id'].isin(['site1', 'site2']))
    
    def test_merge_with_missing_data(self):
        """Test merging when one dataset has missing entries."""
        precip_df = pd.DataFrame({
            'site_id': ['site1', 'site1'],
            'date': pd.to_datetime(['2020-01-01', '2020-02-01']),
            'precip_mm': [10.5, 15.2]
        })
        
        temp_df = pd.DataFrame({
            'site_id': ['site1', 'site2'],
            'date': pd.to_datetime(['2020-01-01', '2020-01-01']),
            'temp_avg_c': [25.0, 20.0]
        })
        
        merged = merge_climate_data(precip_df, temp_df)
        
        # Should have 3 rows (site1 Jan, site1 Feb, site2 Jan)
        # But site2 Feb precip is missing, site1 Feb temp is missing
        assert len(merged) == 3
    
    def test_merge_both_none(self):
        """Test that merging two None values raises error."""
        with pytest.raises(ValueError, match="Both precipitation and temperature data are None"):
            merge_climate_data(None, None)
    
    def test_merge_one_none(self):
        """Test merging when one dataset is None."""
        precip_df = pd.DataFrame({
            'site_id': ['site1'],
            'date': pd.to_datetime(['2020-01-01']),
            'precip_mm': [10.5]
        })
        
        # Should return the non-None dataframe
        result = merge_climate_data(precip_df, None)
        assert len(result) == 1
        assert 'precip_mm' in result.columns
        
        result = merge_climate_data(None, precip_df)
        assert len(result) == 1
        assert 'precip_mm' in result.columns

class TestClimateDataSchema:
    """Test cases for climate data schema validation."""
    
    def test_required_columns(self):
        """Test that merged data has required columns."""
        precip_df = pd.DataFrame({
            'site_id': ['site1'],
            'date': pd.to_datetime(['2020-01-01']),
            'precip_mm': [10.5]
        })
        
        temp_df = pd.DataFrame({
            'site_id': ['site1'],
            'date': pd.to_datetime(['2020-01-01']),
            'temp_avg_c': [25.0]
        })
        
        merged = merge_climate_data(precip_df, temp_df)
        
        required_cols = ['site_id', 'date']
        for col in required_cols:
            assert col in merged.columns, f"Missing required column: {col}"
    
    def test_data_types(self):
        """Test that data types are correct."""
        precip_df = pd.DataFrame({
            'site_id': ['site1'],
            'date': pd.to_datetime(['2020-01-01']),
            'precip_mm': [10.5]
        })
        
        temp_df = pd.DataFrame({
            'site_id': ['site1'],
            'date': pd.to_datetime(['2020-01-01']),
            'temp_avg_c': [25.0]
        })
        
        merged = merge_climate_data(precip_df, temp_df)
        
        assert pd.api.types.is_datetime64_any_dtype(merged['date'])
        assert pd.api.types.is_numeric_dtype(merged['precip_mm'])
        assert pd.api.types.is_numeric_dtype(merged['temp_avg_c'])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
