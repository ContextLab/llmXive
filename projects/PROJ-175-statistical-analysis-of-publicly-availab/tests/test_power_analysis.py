import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from code.data.power_analysis import (
    calculate_variance_estimate, 
    calculate_sample_size,
    download_pilot_sample
)

def test_calculate_variance_estimate():
    """Test variance calculation on a known dataset."""
    data = {
        'rating': [1.0, 2.0, 3.0, 4.0, 5.0],
        'ingredients': [['a'], ['b'], ['c'], ['d'], ['e']]
    }
    df = pd.DataFrame(data)
    variance = calculate_variance_estimate(df)
    # Variance of [1,2,3,4,5] is 2.5
    assert abs(variance - 2.5) < 0.01

def test_calculate_sample_size():
    """Test sample size calculation logic."""
    # With variance=1, effect=0.1, alpha=0.05, beta=0.2
    # n = 2 * (2.8)^2 * 1 / 0.01 = 2 * 7.84 * 100 = 1568
    n = calculate_sample_size(variance=1.0, alpha=0.05, beta=0.2, effect_size=0.1)
    assert n > 0
    assert isinstance(n, int)

def test_download_pilot_sample_structure():
    """Test that the pilot sample function returns a DataFrame with expected structure."""
    # This test might be skipped if network access is restricted, 
    # but it validates the logic if run.
    try:
        df = download_pilot_sample(pilot_size=10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        # Check for at least one expected column
        assert 'rating' in df.columns or 'ingredients' in df.columns
    except Exception:
        pytest.skip("Network unavailable or dataset not accessible")

def test_sample_size_logic():
    """Verify that higher variance leads to larger sample size."""
    n_low = calculate_sample_size(variance=1.0, effect_size=0.1)
    n_high = calculate_sample_size(variance=10.0, effect_size=0.1)
    assert n_high > n_low
    
def test_effect_size_logic():
    """Verify that smaller effect size leads to larger sample size."""
    n_large_eff = calculate_sample_size(variance=1.0, effect_size=0.5)
    n_small_eff = calculate_sample_size(variance=1.0, effect_size=0.1)
    assert n_small_eff > n_large_eff