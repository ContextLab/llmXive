import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path if running standalone
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.frequentist import simple_average, weighted_average

class TestSimpleAverage:
    def test_simple_average_basic(self):
        data = {
            'week_bin': ['W1', 'W1', 'W2', 'W2'],
            'vote_share': [50.0, 52.0, 48.0, 50.0]
        }
        df = pd.DataFrame(data)
        result = simple_average(df, bin_col='week_bin', value_col='vote_share')
        
        assert len(result) == 2
        assert result.loc[result['week_bin'] == 'W1', 'simple_avg_forecast'].iloc[0] == 51.0
        assert result.loc[result['week_bin'] == 'W2', 'simple_avg_forecast'].iloc[0] == 49.0
        assert result['count'].sum() == 4

    def test_simple_average_empty(self):
        df = pd.DataFrame(columns=['week_bin', 'vote_share'])
        result = simple_average(df)
        assert result.empty

    def test_simple_average_single_row(self):
        data = {
            'week_bin': ['W1'],
            'vote_share': [55.0]
        }
        df = pd.DataFrame(data)
        result = simple_average(df)
        assert result['simple_avg_forecast'].iloc[0] == 55.0

class TestWeightedAverage:
    def test_weighted_average_basic(self):
        # Poll 1: 50%, RMSE 2.0 -> inv 0.5
        # Poll 2: 52%, RMSE 1.0 -> inv 1.0
        # Total inv = 1.5
        # Weighted = (50*0.5 + 52*1.0) / 1.5 = (25 + 52) / 1.5 = 77 / 1.5 = 51.333
        data = {
            'week_bin': ['W1', 'W1'],
            'vote_share': [50.0, 52.0],
            'historical_rmse': [2.0, 1.0]
        }
        df = pd.DataFrame(data)
        result = weighted_average(df, bin_col='week_bin', value_col='vote_share', weight_col='historical_rmse')
        
        expected = (50.0 * 0.5 + 52.0 * 1.0) / 1.5
        assert np.isclose(result['weighted_avg_forecast'].iloc[0], expected, rtol=1e-5)
        assert result['total_weight'].iloc[0] == 1.5

    def test_weighted_average_zero_rmse_handling(self):
        # If RMSE is 0, inv_rmse becomes inf, then we handle it.
        # In our implementation, we replace 0 with NaN, then fill NaN inv_rmse with 0.
        # So a row with RMSE=0 gets 0 weight.
        data = {
            'week_bin': ['W1', 'W1'],
            'vote_share': [50.0, 52.0],
            'historical_rmse': [0.0, 1.0] # 0.0 should result in 0 weight
        }
        df = pd.DataFrame(data)
        result = weighted_average(df)
        
        # Only the second row should contribute
        # Weighted = (52.0 * 1.0) / 1.0 = 52.0
        assert np.isclose(result['weighted_avg_forecast'].iloc[0], 52.0, rtol=1e-5)
        assert result['total_weight'].iloc[0] == 1.0

    def test_weighted_average_nan_rmse_handling(self):
        # If RMSE is NaN, inv_rmse is NaN, then filled with 0.
        data = {
            'week_bin': ['W1', 'W1'],
            'vote_share': [50.0, 52.0],
            'historical_rmse': [np.nan, 1.0]
        }
        df = pd.DataFrame(data)
        result = weighted_average(df)
        
        # Only the second row contributes
        assert np.isclose(result['weighted_avg_forecast'].iloc[0], 52.0, rtol=1e-5)

    def test_weighted_average_empty(self):
        df = pd.DataFrame(columns=['week_bin', 'vote_share', 'historical_rmse'])
        result = weighted_average(df)
        assert result.empty

    def test_weighted_average_all_zero_weights(self):
        # If all weights are 0 (e.g., all RMSEs were 0 or NaN)
        data = {
            'week_bin': ['W1', 'W1'],
            'vote_share': [50.0, 52.0],
            'historical_rmse': [0.0, 0.0]
        }
        df = pd.DataFrame(data)
        result = weighted_average(df)
        
        # Should result in NaN forecast
        assert np.isnan(result['weighted_avg_forecast'].iloc[0])