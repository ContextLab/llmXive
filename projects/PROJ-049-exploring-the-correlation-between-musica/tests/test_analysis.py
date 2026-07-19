import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis import log_transform_column, compute_spearman_correlations

def test_log_transform_column():
    """Test that log_transform_column correctly applies log1p to listening_minutes."""
    data = {
        'user_id': [1, 2, 3],
        'listening_minutes': [0, 100, 10000]
    }
    df = pd.DataFrame(data)
    
    result = log_transform_column(df, 'listening_minutes')
    
    assert 'listening_minutes_log' in result.columns
    assert result['listening_minutes_log'][0] == np.log1p(0)
    assert result['listening_minutes_log'][1] == pytest.approx(np.log1p(100))
    assert result['listening_minutes_log'][2] == pytest.approx(np.log1p(10000))

def test_compute_spearman_correlations():
    """Test Spearman correlation computation with known ground truth."""
    # Create a synthetic dataset with known correlation
    np.random.seed(42)
    n = 100
    # Generate two perfectly correlated variables
    x = np.random.rand(n)
    y = x + np.random.normal(0, 0.1, n)  # Strong positive correlation
    
    df = pd.DataFrame({
        'trait_A': x,
        'genre_B': y
    })
    
    result = compute_spearman_correlations(df, ['trait_A'], ['genre_B'], 'dummy')
    
    assert len(result) == 1
    assert result['trait'].iloc[0] == 'trait_A'
    assert result['genre'].iloc[0] == 'genre_B'
    # Spearman rho should be very close to 1.0
    assert result['rho'].iloc[0] > 0.95
    assert result['p_value'].iloc[0] < 0.05

def test_compute_spearman_correlations_insufficient_data():
    """Test handling of insufficient data (less than 2 points)."""
    df = pd.DataFrame({
        'trait_A': [1.0],
        'genre_B': [2.0]
    })
    
    # Should not raise, just skip and return empty or partial results
    result = compute_spearman_correlations(df, ['trait_A'], ['genre_B'], 'dummy')
    
    # With only 1 row, correlation cannot be computed, so result should be empty
    assert len(result) == 0
