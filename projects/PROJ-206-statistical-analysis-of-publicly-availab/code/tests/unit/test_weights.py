import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.data.weights import calculate_historical_rmse, assign_weights, DEFAULT_MEDIAN_WEIGHT

class TestHistoricalRMSE:
    """Tests for the calculate_historical_rmse function"""
    
    def test_calculate_rmse_basic(self):
        """Test basic RMSE calculation with known values"""
        # Create test data with known errors
        data = {
            'pollster': ['A', 'A', 'B', 'B'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'],
            'vote_share': [50.0, 52.0, 48.0, 51.0],
            'actual_result': [50.0, 50.0, 50.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        rmse_df = calculate_historical_rmse(df)
        
        # Pollster A: errors = [0, 2], RMSE = sqrt((0 + 4)/2) = sqrt(2) ≈ 1.414
        # Pollster B: errors = [-2, 1], RMSE = sqrt((4 + 1)/2) = sqrt(2.5) ≈ 1.581
        
        assert len(rmse_df) == 2
        assert 'pollster' in rmse_df.columns
        assert 'historical_rmse' in rmse_df.columns
        assert 'poll_count' in rmse_df.columns
        
        # Check specific values
        rmse_a = rmse_df[rmse_df['pollster'] == 'A']['historical_rmse'].values[0]
        rmse_b = rmse_df[rmse_df['pollster'] == 'B']['historical_rmse'].values[0]
        
        assert np.isclose(rmse_a, np.sqrt(2), rtol=1e-5)
        assert np.isclose(rmse_b, np.sqrt(2.5), rtol=1e-5)
    
    def test_calculate_rmse_single_poll(self):
        """Test RMSE calculation with only one poll per pollster"""
        data = {
            'pollster': ['A', 'B'],
            'date': ['2024-01-01', '2024-01-02'],
            'vote_share': [50.0, 48.0],
            'actual_result': [50.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        rmse_df = calculate_historical_rmse(df)
        
        # With only one poll, RMSE cannot be calculated (need at least 2)
        # The function should skip these pollsters
        assert len(rmse_df) == 0
    
    def test_calculate_rmse_zero_error(self):
        """Test RMSE calculation when all polls are perfect"""
        data = {
            'pollster': ['A', 'A', 'A'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'vote_share': [50.0, 50.0, 50.0],
            'actual_result': [50.0, 50.0, 50.0]
        }
        df = pd.DataFrame(data)
        
        rmse_df = calculate_historical_rmse(df)
        
        # All errors are 0, so RMSE should be 0
        assert len(rmse_df) == 1
        assert np.isclose(rmse_df['historical_rmse'].values[0], 0.0)
    
    def test_calculate_rmse_empty_dataframe(self):
        """Test RMSE calculation with empty DataFrame"""
        df = pd.DataFrame(columns=['pollster', 'date', 'vote_share', 'actual_result'])
        
        rmse_df = calculate_historical_rmse(df)
        
        assert len(rmse_df) == 0

class TestWeightAssignment:
    """Tests for the assign_weights function"""
    
    def test_assign_weights_basic(self):
        """Test basic weight assignment with known RMSE values"""
        # Create test data
        df = pd.DataFrame({
            'pollster': ['A', 'A', 'B', 'B'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-01', '2024-01-02'],
            'vote_share': [50.0, 52.0, 48.0, 51.0]
        })
        
        # Create RMSE DataFrame
        rmse_df = pd.DataFrame({
            'pollster': ['A', 'B'],
            'historical_rmse': [1.0, 2.0]  # A is more accurate
        })
        
        df_weighted = assign_weights(df, rmse_df)
        
        # Check that weights are assigned
        assert 'weight' in df_weighted.columns
        assert len(df_weighted) == 4
        
        # Check that weights sum to 1.0
        assert np.isclose(df_weighted['weight'].sum(), 1.0)
        
        # Pollster A should have higher weights than B (lower RMSE)
        weight_a = df_weighted[df_weighted['pollster'] == 'A']['weight'].sum()
        weight_b = df_weighted[df_weighted['pollster'] == 'B']['weight'].sum()
        
        assert weight_a > weight_b
    
    def test_assign_weights_no_history(self):
        """Test weight assignment for pollsters with no history"""
        df = pd.DataFrame({
            'pollster': ['A', 'B', 'C'],  # C has no history
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'vote_share': [50.0, 52.0, 48.0]
        })
        
        rmse_df = pd.DataFrame({
            'pollster': ['A', 'B'],
            'historical_rmse': [1.0, 2.0]
        })
        
        df_weighted = assign_weights(df, rmse_df)
        
        # Check that weights are assigned to all
        assert 'weight' in df_weighted.columns
        assert len(df_weighted) == 3
        assert np.isclose(df_weighted['weight'].sum(), 1.0)
        
        # Pollster C should have the default median weight
        weight_c = df_weighted[df_weighted['pollster'] == 'C']['weight'].values[0]
        assert weight_c > 0
    
    def test_assign_weights_zero_rmse(self):
        """Test weight assignment when RMSE is zero (prevents division by zero)"""
        df = pd.DataFrame({
            'pollster': ['A', 'B'],
            'date': ['2024-01-01', '2024-01-02'],
            'vote_share': [50.0, 52.0]
        })
        
        rmse_df = pd.DataFrame({
            'pollster': ['A', 'B'],
            'historical_rmse': [0.0, 1.0]  # A has zero RMSE
        })
        
        # This should not raise a division by zero error
        df_weighted = assign_weights(df, rmse_df)
        
        assert 'weight' in df_weighted.columns
        assert np.isclose(df_weighted['weight'].sum(), 1.0)
        
        # Both should have valid weights
        assert all(df_weighted['weight'] > 0)
    
    def test_assign_weights_empty_rmse(self):
        """Test weight assignment when RMSE DataFrame is empty"""
        df = pd.DataFrame({
            'pollster': ['A', 'B', 'C'],
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'vote_share': [50.0, 52.0, 48.0]
        })
        
        rmse_df = pd.DataFrame(columns=['pollster', 'historical_rmse'])
        
        df_weighted = assign_weights(df, rmse_df)
        
        # All should get default median weight, then normalized
        assert 'weight' in df_weighted.columns
        assert len(df_weighted) == 3
        assert np.isclose(df_weighted['weight'].sum(), 1.0)
        
        # All weights should be equal (normalized default)
        expected_weight = 1.0 / 3
        for weight in df_weighted['weight']:
            assert np.isclose(weight, expected_weight)
    
    def test_assign_weights_single_poll(self):
        """Test weight assignment with a single poll"""
        df = pd.DataFrame({
            'pollster': ['A'],
            'date': ['2024-01-01'],
            'vote_share': [50.0]
        })
        
        rmse_df = pd.DataFrame({
            'pollster': ['A'],
            'historical_rmse': [1.0]
        })
        
        df_weighted = assign_weights(df, rmse_df)
        
        assert len(df_weighted) == 1
        assert df_weighted['weight'].values[0] == 1.0  # Single poll gets weight 1.0