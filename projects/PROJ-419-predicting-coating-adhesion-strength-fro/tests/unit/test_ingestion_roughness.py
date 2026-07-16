import pytest
import pandas as pd
import numpy as np
from ingestion import exclude_missing_surface_roughness

class TestExcludeMissingSurfaceRoughness:
    
    def test_exclude_records_with_high_missing_ratio(self):
        """Test that records with >50% missing roughness data are excluded."""
        data = {
            'id': [1, 2, 3],
            'RMS': [0.5, np.nan, np.nan],
            'Ra': [0.2, np.nan, np.nan],
            'Rz': [0.8, np.nan, np.nan],
            'adhesion_strength': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        # Record 1: 0 missing (keep)
        # Record 2: 3 missing out of 3 (100% > 50% -> exclude)
        # Record 3: 3 missing out of 3 (100% > 50% -> exclude)
        
        result = exclude_missing_surface_roughness(df)
        
        assert len(result) == 1
        assert result.iloc[0]['id'] == 1
        assert result.iloc[0]['adhesion_strength'] == 10.0

    def test_impute_median_for_remaining_missing(self):
        """Test that remaining missing values are imputed with column median."""
        data = {
            'id': [1, 2, 3],
            'RMS': [0.5, 1.0, np.nan],
            'Ra': [0.2, np.nan, 0.4],
            'Rz': [0.8, 1.5, 2.0],
            'adhesion_strength': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        # Record 2: 1 missing Ra (33% < 50% -> keep, impute)
        # Record 3: 1 missing RMS (33% < 50% -> keep, impute)
        
        result = exclude_missing_surface_roughness(df)
        
        assert len(result) == 3
        
        # Check imputation for Ra (median of 0.2 and 0.4 is 0.3)
        assert result.iloc[1]['Ra'] == 0.3
        
        # Check imputation for RMS (median of 0.5 and 1.0 is 0.75)
        assert result.iloc[2]['RMS'] == 0.75

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['RMS', 'Ra', 'adhesion_strength'])
        result = exclude_missing_surface_roughness(df)
        assert result.empty

    def test_no_roughness_columns(self):
        """Test handling of dataframe with no roughness columns."""
        data = {
            'id': [1, 2],
            'adhesion_strength': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        result = exclude_missing_surface_roughness(df)
        # Should return as-is since no roughness columns to check
        assert len(result) == 2

    def test_threshold_parameter(self):
        """Test that the threshold parameter works correctly."""
        data = {
            'id': [1, 2],
            'RMS': [0.5, np.nan],
            'Ra': [0.2, np.nan],
            'Rz': [0.8, np.nan],
            'adhesion_strength': [10.0, 20.0]
        }
        df = pd.DataFrame(data)
        
        # With default threshold (0.5), record 2 (100% missing) is excluded
        result_default = exclude_missing_surface_roughness(df, threshold=0.5)
        assert len(result_default) == 1
        
        # With high threshold (0.9), record 2 (100% missing) is still excluded (100% > 90%)
        result_high = exclude_missing_surface_roughness(df, threshold=0.9)
        assert len(result_high) == 1
        
        # If we had 2 out of 3 missing (66%), threshold 0.6 would exclude, 0.7 would keep
        data_partial = {
            'id': [1, 2],
            'RMS': [0.5, np.nan],
            'Ra': [0.2, np.nan],
            'Rz': [0.8, 1.5], # 1 missing out of 3 = 33%
            'adhesion_strength': [10.0, 20.0]
        }
        df_partial = pd.DataFrame(data_partial)
        result_keep = exclude_missing_surface_roughness(df_partial, threshold=0.4)
        assert len(result_keep) == 2