"""
Unit tests for data_loader.py (T012a)
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.data_loader import _generate_synthetic_data, _fetch_with_retry, load_game_data
from config import RANDOM_SEED

def test_synthetic_data_generation():
    """Test that synthetic data generator creates valid DataFrame with expected columns."""
    df = _generate_synthetic_data()
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    
    # Check for essential columns
    required_cols = ['gameID', 'date', 'yearID', 'teamID_home', 'teamID_vis', 'W', 'L']
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check data types
    assert df['yearID'].dtype in ['int64', 'int32']
    assert df['W'].dtype in ['int64', 'int32']
    assert df['L'].dtype in ['int64', 'int32']
    
    # Check constraints
    assert (df['teamID_home'] != df['teamID_vis']).all(), "Home and Visiting teams must differ"
    assert (df['W'] >= 0).all(), "Wins cannot be negative"
    assert (df['L'] >= 0).all(), "Losses cannot be negative"

def test_fetch_with_retry_timeout():
    """Test that timeout triggers fallback logic (mocked)."""
    with patch('code.data_loader.requests.get') as mock_get:
        mock_get.side_effect = Exception("Connection Timeout")
        
        result = _fetch_with_retry("http://fake-url.com", timeout=1)
        assert result is None, "Should return None on persistent failure"

def test_load_game_data_real_success():
    """Test loading real data when mock returns success."""
    mock_df = pd.DataFrame({
        'gameID': ['G1'],
        'date': ['2020-01-01'],
        'yearID': [2020],
        'teamID_home': ['NYY'],
        'teamID_vis': ['BOS'],
        'W': [1],
        'L': [0],
        'R': [5],
        'RA': [2]
    })

    with patch('code.data_loader._fetch_with_retry', return_value=mock_df):
        df, is_real = load_game_data()
        
        assert is_real is True
        assert len(df) == 1
        assert df.iloc[0]['teamID_home'] == 'NYY'

def test_load_game_data_fallback():
    """Test that load_game_data falls back to synthetic when fetch fails."""
    with patch('code.data_loader._fetch_with_retry', return_value=None):
        df, is_real = load_game_data()
        
        assert is_real is False
        assert len(df) > 0
        assert 'gameID' in df.columns

def test_load_game_data_force_synthetic():
    """Test force_synthetic flag."""
    df, is_real = load_game_data(force_synthetic=True)
    
    assert is_real is False
    assert len(df) > 0
