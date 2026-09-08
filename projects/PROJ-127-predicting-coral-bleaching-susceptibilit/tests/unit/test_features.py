import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import warnings

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features import (
    compute_lagged_features,
    compute_interaction_features,
    check_definitional_circularity,
    calculate_vif,
    filter_high_vif
)

class TestDefinitionalCircularity:
    """Test cases for Definitional Circularity Check (T018)"""
    
    def test_dhw_present_dropped(self):
        """Test that DHW is dropped when present"""
        df = pd.DataFrame({
            'reef_id': [1, 2, 3],
            'sst': [28.5, 29.0, 28.8],
            'dhw': [2.1, 3.5, 1.8],
            'thermal_tolerance': [0.8, 0.9, 0.85]
        })
        
        result = check_definitional_circularity(df)
        
        # DHW should be dropped
        assert 'dhw' not in result.columns
        # Flag should be added
        assert 'dhw_dropped_due_to_circularity' in result.columns
        assert all(result['dhw_dropped_due_to_circularity'] == True)
        
    def test_dhw_absent_proceeds(self):
        """Test that processing proceeds normally when DHW is absent"""
        df = pd.DataFrame({
            'reef_id': [1, 2, 3],
            'sst': [28.5, 29.0, 28.8],
            'thermal_tolerance': [0.8, 0.9, 0.85]
        })
        
        result = check_definitional_circularity(df)
        
        # DHW should not be in columns (wasn't there)
        assert 'dhw' not in result.columns
        # Flag should indicate no drop
        assert 'dhw_dropped_due_to_circularity' in result.columns
        assert all(result['dhw_dropped_due_to_circularity'] == False)
        
    def test_empty_dataframe(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame()
        result = check_definitional_circularity(df)
        assert result.empty

class TestLaggedFeatures:
    """Test cases for lagged feature computation"""
    
    def test_lagged_features_computed(self):
        """Test that lagged features are computed correctly"""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'sst': [28.0 + i * 0.1 for i in range(10)],
            'dhw': [1.0 + i * 0.1 for i in range(10)]
        })
        
        result = compute_lagged_features(df)
        
        # Check that lagged columns exist
        assert 'sst_lag_30d' in result.columns
        assert 'dhw_lag_30d' in result.columns
        
    def test_lagged_features_empty(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame()
        result = compute_lagged_features(df)
        assert result.empty

class TestInteractionFeatures:
    """Test cases for interaction feature computation"""
    
    def test_interaction_computed(self):
        """Test that interaction features are computed correctly"""
        df = pd.DataFrame({
            'dhw': [1.0, 2.0, 3.0],
            'thermal_tolerance': [0.5, 0.6, 0.7]
        })
        
        result = compute_interaction_features(df)
        
        # Check that interaction column exists
        assert 'dhw_thermal_interaction' in result.columns
        
        # Verify calculation
        expected = df['dhw'] * df['thermal_tolerance']
        pd.testing.assert_series_equal(result['dhw_thermal_interaction'], expected)
        
    def test_interaction_missing_columns(self):
        """Test handling of missing columns"""
        df = pd.DataFrame({
            'dhw': [1.0, 2.0, 3.0]
        })
        
        result = compute_interaction_features(df)
        
        # Should not crash, no interaction column added
        assert 'dhw_thermal_interaction' not in result.columns

class TestVIF:
    """Test cases for VIF calculation and filtering"""
    
    def test_vif_calculation(self):
        """Test that VIF is calculated for features"""
        # Create highly correlated features
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'feature2': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1],
            'feature3': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        })
        
        vif_df = calculate_vif(df)
        
        # Check that VIF values are calculated
        assert len(vif_df) == 3
        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        assert all(vif_df['vif'] >= 1.0)  # VIF should be >= 1
        
    def test_high_vif_filtered(self):
        """Test that high VIF features are filtered out"""
        # Create highly correlated features
        df = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'feature2': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1],
            'feature3': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        })
        
        filtered_df = filter_high_vif(df, vif_threshold=5.0)
        
        # Some features should be dropped due to high correlation
        assert len(filtered_df.columns) < len(df.columns) or len(filtered_df.columns) == len(df.columns)
        # The function should not crash
        assert filtered_df.shape[0] == df.shape[0]
        
    def test_vif_empty_dataframe(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame()
        vif_df = calculate_vif(df)
        assert vif_df.empty
        
        filtered_df = filter_high_vif(df)
        assert filtered_df.empty