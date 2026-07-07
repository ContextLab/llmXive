import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from feature_engineering import calculate_advanced_metrics, calculate_traditional_metrics

def test_woba_calculation():
    """Test that wOBA is calculated correctly based on the formula."""
    data = {
        'bb': [1], 'hbp': [0], 'single': [1], 'double': [0], 'triple': [0], 'hr': [0],
        'ab': [3], 'sf': [0], 'ibb': [0], 'k': [1] # k not used in wOBA denom but in BABIP
    }
    df = pd.DataFrame(data)
    
    result = calculate_advanced_metrics(df)
    
    # Expected wOBA numerator: 0.69*1 + 0.72*0 + 0.89*1 + ... = 1.58
    # Denominator: 3 + 1 + 0 + 0 + 0 = 4
    # Expected wOBA: 1.58 / 4 = 0.395
    expected_woba = (0.69 * 1 + 0.89 * 1) / (3 + 1)
    
    assert np.isclose(result['woba'].iloc[0], expected_woba, rtol=1e-5), \
        f"Expected wOBA {expected_woba}, got {result['woba'].iloc[0]}"

def test_babip_calculation():
    """Test that BABIP is calculated correctly."""
    # H = 1B + 2B + 3B + HR
    # BABIP = (H - HR) / (AB - K + SF + HR)
    data = {
        'bb': [0], 'hbp': [0], 'single': [1], 'double': [0], 'triple': [0], 'hr': [1],
        'ab': [5], 'k': [2], 'sf': [0], 'ibb': [0], 'park_factor': [1.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_advanced_metrics(df)
    
    # H = 1 + 1 = 2
    # Num = 2 - 1 = 1
    # Den = 5 - 2 + 0 + 1 = 4
    # BABIP = 0.25
    expected_babip = 0.25
    
    assert np.isclose(result['babip'].iloc[0], expected_babip, rtol=1e-5), \
        f"Expected BABIP {expected_babip}, got {result['babip'].iloc[0]}"

def test_park_adjusted_re():
    """Test that park-adjusted run expectancy is affected by park factor."""
    data = {
        'bb': [0], 'hbp': [0], 'single': [0], 'double': [0], 'triple': [0], 'hr': [1],
        'ab': [1], 'k': [0], 'sf': [0], 'ibb': [0], 'park_factor': [1.2] # 20% hitter friendly
    }
    df = pd.DataFrame(data)
    
    result = calculate_advanced_metrics(df)
    
    # Raw RE for HR: 1.40
    # Adjusted: 1.40 * 1.2 = 1.68
    # Note: This is a simplified test; actual formula includes outs and other events.
    # We just verify the multiplication happens.
    assert result['park_adj_re'].iloc[0] > 1.40, \
        "Park adjusted RE should be higher than raw RE for a hitter-friendly park."

def test_division_by_zero_handling():
    """Test that metrics handle division by zero gracefully (fill with 0 or NaN)."""
    data = {
        'bb': [0], 'hbp': [0], 'single': [0], 'double': [0], 'triple': [0], 'hr': [0],
        'ab': [0], 'k': [0], 'sf': [0], 'ibb': [0], 'hits': [0], 'hits': [0], 'park_factor': [1.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_advanced_metrics(df)
    
    # Should not raise an error
    assert not result['woba'].isna().all() or result['woba'].iloc[0] == 0
    assert not result['babip'].isna().all() or result['babip'].iloc[0] == 0

def test_traditional_metrics_avoid_div_zero():
    """Test that traditional metrics handle 0 at-bats/innings."""
    data = {
        'hits': [0], 'at_bats': [0], 'earned_runs': [0], 'innings_pitched': [0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_traditional_metrics(df)
    
    # Should not raise error, values should be 0 or NaN handled
    assert result['avg'].iloc[0] == 0 or pd.isna(result['avg'].iloc[0])
    assert result['era'].iloc[0] == 0 or pd.isna(result['era'].iloc[0])