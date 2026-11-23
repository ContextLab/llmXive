import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lag_decay_analysis import (
    differencing_sentiment,
    compute_sentiment_trend_relative_to_revenue
)

class TestDifferencingSentiment:
    def test_differencing_sentiment_basic(self):
        """Test basic differencing functionality"""
        data = {
            'genre': ['Action', 'Action', 'Drama', 'Drama'],
            'week_number': [1, 2, 1, 2],
            'sentiment_score': [0.5, 0.6, 0.3, 0.4]
        }
        df = pd.DataFrame(data)
        
        result = differencing_sentiment(df)
        
        assert 'sentiment_diff' in result.columns
        # First week of each genre should be 0 (filled NaN)
        assert result.loc[result['week_number'] == 1, 'sentiment_diff'].sum() == 0
        # Second week should be the difference
        assert result.loc[(result['genre'] == 'Action') & (result['week_number'] == 2), 'sentiment_diff'].iloc[0] == 0.1
        assert result.loc[(result['genre'] == 'Drama') & (result['week_number'] == 2), 'sentiment_diff'].iloc[0] == 0.1

    def test_differencing_sentiment_missing_column(self):
        """Test that differencing fails with missing sentiment_score column"""
        data = {
            'genre': ['Action', 'Drama'],
            'week_number': [1, 1]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="DataFrame must contain 'sentiment_score' column"):
            differencing_sentiment(df)

class TestComputeSentimentTrendRelativeToRevenue:
    def test_compute_correlation_basic(self):
        """Test basic correlation computation"""
        data = {
            'genre': ['Action', 'Drama', 'Comedy'],
            'sentiment_score': [0.5, 0.3, 0.7],
            'opening_weekend_revenue': [1000000, 500000, 1200000]
        }
        df = pd.DataFrame(data)
        
        result = compute_sentiment_trend_relative_to_revenue(df)
        
        assert 'correlation' in result.columns
        assert 'p_value' in result.columns
        assert len(result) == 3
        # Check that correlation is a valid number between -1 and 1
        assert -1 <= result['correlation'].iloc[0] <= 1

    def test_compute_correlation_insufficient_data(self):
        """Test correlation with only one genre"""
        data = {
            'genre': ['Action'],
            'sentiment_score': [0.5],
            'opening_weekend_revenue': [1000000]
        }
        df = pd.DataFrame(data)
        
        result = compute_sentiment_trend_relative_to_revenue(df)
        
        assert pd.isna(result['correlation'].iloc[0])
        assert pd.isna(result['p_value'].iloc[0])

    def test_compute_correlation_missing_columns(self):
        """Test that correlation fails with missing required columns"""
        data = {
            'genre': ['Action', 'Drama'],
            'sentiment_score': [0.5, 0.3]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="DataFrame missing required columns"):
            compute_sentiment_trend_relative_to_revenue(df)

    def test_compute_correlation_zero_variance(self):
        """Test correlation when one variable has zero variance"""
        data = {
            'genre': ['Action', 'Drama', 'Comedy'],
            'sentiment_score': [0.5, 0.5, 0.5],  # Constant sentiment
            'opening_weekend_revenue': [1000000, 500000, 1200000]
        }
        df = pd.DataFrame(data)
        
        result = compute_sentiment_trend_relative_to_revenue(df)
        
        assert pd.isna(result['correlation'].iloc[0])
        assert pd.isna(result['p_value'].iloc[0])
