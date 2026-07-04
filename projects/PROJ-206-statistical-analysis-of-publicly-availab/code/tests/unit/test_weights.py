import os
import sys
import tempfile
import math
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.weights import calculate_historical_rmse, assign_weights_with_fallback

def test_calculate_historical_rmse():
    """Test RMSE calculation with strict temporal split."""
    # Create mock data
    # Cycle 2020 data
    poll_2020 = [
        {'pollster': 'A', 'cycle': '2020', 'candidate': 'X', 'vote_share': 50.0},
        {'pollster': 'B', 'cycle': '2020', 'candidate': 'X', 'vote_share': 52.0},
    ]
    # Cycle 2024 data
    poll_2024 = [
        {'pollster': 'A', 'cycle': '2024', 'candidate': 'X', 'vote_share': 48.0},
        {'pollster': 'C', 'cycle': '2024', 'candidate': 'X', 'vote_share': 49.0},
    ]
    
    # Outcomes
    outcome_2020 = {'cycle': '2020', 'candidate': 'X', 'vote_share': 51.0}
    outcome_2024 = {'cycle': '2024', 'candidate': 'X', 'vote_share': 49.0}
    
    all_polls = poll_2020 + poll_2024
    outcomes = [outcome_2020, outcome_2024]
    
    # Calculate RMSE for 2024 using only 2020 data
    rmse_map = calculate_historical_rmse(all_polls, outcomes, '2024')
    
    # Pollster A: 2020 error = 50 - 51 = -1 -> sq = 1. RMSE = sqrt(1) = 1.0
    # Pollster B: 2020 error = 52 - 51 = 1 -> sq = 1. RMSE = 1.0
    # Pollster C: No history in 2020, should not be in map
    
    assert 'A' in rmse_map
    assert math.isclose(rmse_map['A'], 1.0)
    assert 'B' in rmse_map
    assert math.isclose(rmse_map['B'], 1.0)
    assert 'C' not in rmse_map

def test_assign_weights_with_fallback():
    """Test weight assignment and fallback logic."""
    polls = [
        {'pollster': 'A', 'vote_share': 50.0},
        {'pollster': 'B', 'vote_share': 51.0},
        {'pollster': 'C', 'vote_share': 49.0}, # No history
    ]
    
    rmse_map = {'A': 1.0, 'B': 2.0}
    
    weighted = assign_weights_with_fallback(polls, rmse_map)
    
    # Check weights
    # A: 1/1.0 = 1.0
    # B: 1/2.0 = 0.5
    # C: Fallback (median of [1.0, 2.0] is 1.5) -> 1/1.5 = 0.666...
    
    w_a = next(p['weight'] for p in weighted if p['pollster'] == 'A')
    w_b = next(p['weight'] for p in weighted if p['pollster'] == 'B')
    w_c = next(p['weight'] for p in weighted if p['pollster'] == 'C')
    
    assert math.isclose(w_a, 1.0)
    assert math.isclose(w_b, 0.5)
    assert math.isclose(w_c, 1.0/1.5, rel_tol=1e-4)
    
    # Check RMSE assignment
    assert weighted[0]['historical_rmse'] == 1.0
    assert weighted[1]['historical_rmse'] == 2.0
    assert weighted[2]['historical_rmse'] == 1.5 # Median fallback

def test_division_by_zero_prevention():
    """Test that zero RMSE does not cause division by zero."""
    polls = [{'pollster': 'A', 'vote_share': 50.0}]
    rmse_map = {'A': 0.0} # Zero RMSE
    
    # Should not raise error
    weighted = assign_weights_with_fallback(polls, rmse_map)
    w_a = weighted[0]['weight']
    
    # Should be a large but finite number due to epsilon
    assert w_a > 0
    assert w_a != float('inf')

def test_empty_history():
    """Test behavior when no historical data exists."""
    polls = [{'pollster': 'A', 'vote_share': 50.0}]
    rmse_map = {}
    
    weighted = assign_weights_with_fallback(polls, rmse_map)
    # Should use default RMSE of 1.0
    assert weighted[0]['historical_rmse'] == 1.0
    assert weighted[0]['weight'] == 1.0
