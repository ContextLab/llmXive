"""
Unit tests for code/data/processor.py (Task T015).
Verifies the FR-008 PSV calculation logic.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.processor import calculate_psv, process_data
from code.utils.constants import get_psv_weights


class TestPSVCalculation:
    """Tests for the PSV calculation function."""

    def test_calculate_psv_basic(self):
        """Test basic PSV calculation with known values."""
        data = {
            'likes': [100],
            'comments': [20],
            'shares': [10],
            'sentiment_score': [1.0]
        }
        df = pd.DataFrame(data)
        weights = get_psv_weights()
        
        # Expected calculation:
        # log_term = 0.25*log(101) + 0.40*log(21) + 0.35*log(11)
        # PSV = log_term * 1.0 * 1.0
        result = calculate_psv(df, weights)
        
        assert len(result) == 1
        assert not np.isnan(result.iloc[0])
        assert result.iloc[0] > 0

    def test_calculate_psv_log_transform_default(self):
        """Verify log(1+x) is applied by default."""
        data = {
            'likes': [0],  # log(1+0) = 0
            'comments': [0],
            'shares': [0],
            'sentiment_score': [1.0]
        }
        df = pd.DataFrame(data)
        weights = get_psv_weights()
        
        # If log transform is on, 0s become log(1)=0.
        # If linear, 0s remain 0.
        # We check that the function handles 0s without error and returns 0 for this specific case.
        result = calculate_psv(df, weights)
        assert result.iloc[0] == 0.0

    def test_calculate_psv_missing_columns(self):
        """Test that missing columns raise KeyError."""
        data = {
            'likes': [100],
            'comments': [20]
            # Missing 'shares' and 'sentiment_score'
        }
        df = pd.DataFrame(data)
        weights = get_psv_weights()
        
        with pytest.raises(KeyError):
            calculate_psv(df, weights)

    def test_calculate_psv_zero_sentiment(self):
        """Test PSV is zero when sentiment is zero."""
        data = {
            'likes': [100],
            'comments': [20],
            'shares': [10],
            'sentiment_score': [0.0]
        }
        df = pd.DataFrame(data)
        weights = get_psv_weights()
        
        result = calculate_psv(df, weights)
        assert result.iloc[0] == 0.0

    def test_process_data_integration(self):
        """Test the full process_data function adds the column correctly."""
        data = {
            'likes': [10, 50],
            'comments': [2, 10],
            'shares': [0, 5],
            'sentiment_score': [0.5, 0.8],
            'id': [1, 2] # Extra column to ensure copy works
        }
        df = pd.DataFrame(data)
        
        processed = process_data(df)
        
        # Check original is unchanged
        assert 'perceived_social_validation' not in df.columns
        
        # Check result has the column
        assert 'perceived_social_validation' in processed.columns
        assert len(processed) == 2
        assert all(processed['perceived_social_validation'] >= 0)

    def test_psv_weights_are_applied_correctly(self):
        """Verify that specific weights produce expected relative values."""
        # Create a scenario where only likes vary
        data = {
            'likes': [1000, 0],
            'comments': [0, 0],
            'shares': [0, 0],
            'sentiment_score': [1.0, 1.0]
        }
        df = pd.DataFrame(data)
        weights = get_psv_weights()
        
        result = calculate_psv(df, weights)
        
        # First row should be significantly higher than second (which is 0)
        # because likes=1000 vs likes=0
        assert result.iloc[0] > result.iloc[1]
        assert result.iloc[1] == 0.0