import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.counterbalance import generate_counterbalance_assignments

def test_counterbalance_balanced():
    """Test balanced allocation (split_ratio=0.5)"""
    df = generate_counterbalance_assignments(n_participants=100, seed=42, split_ratio=0.5)

    # Check columns exist
    assert 'participant_id' in df.columns
    assert 'session_order' in df.columns

    # Check counts are roughly equal (allowing for integer rounding)
    low_first = len(df[df['session_order'] == 'Low-High'])
    high_first = len(df[df['session_order'] == 'High-Low'])

    # With 100 participants and 0.5 ratio, should be exactly 50/50
    assert low_first == 50
    assert high_first == 50

    # Check all participant IDs are unique
    assert df['participant_id'].nunique() == 100

    # Check format of participant IDs
    assert all(p.startswith('P') and len(p) == 4 for p in df['participant_id'])

def test_counterbalance_skewed():
    """Test skewed allocation (split_ratio=0.8)"""
    df = generate_counterbalance_assignments(n_participants=100, seed=42, split_ratio=0.8)

    low_first = len(df[df['session_order'] == 'Low-High'])
    high_first = len(df[df['session_order'] == 'High-Low'])

    # With 100 participants and 0.8 ratio, should be 80/20
    assert low_first == 80
    assert high_first == 20

def test_counterbalance_reproducibility():
    """Test that same seed produces same results"""
    df1 = generate_counterbalance_assignments(n_participants=50, seed=123, split_ratio=0.5)
    df2 = generate_counterbalance_assignments(n_participants=50, seed=123, split_ratio=0.5)

    pd.testing.assert_frame_equal(df1, df2)

def test_counterbalance_different_seeds():
    """Test that different seeds produce different results"""
    df1 = generate_counterbalance_assignments(n_participants=50, seed=123, split_ratio=0.5)
    df2 = generate_counterbalance_assignments(n_participants=50, seed=456, split_ratio=0.5)

    # They should not be identical
    assert not df1.equals(df2)

def test_counterbalance_invalid_ratio():
    """Test that invalid split ratio raises error"""
    with pytest.raises(ValueError):
        generate_counterbalance_assignments(n_participants=50, seed=42, split_ratio=1.5)

def test_counterbalance_small_sample():
    """Test with small sample size"""
    df = generate_counterbalance_assignments(n_participants=2, seed=42, split_ratio=0.5)
    assert len(df) == 2
    assert df['participant_id'].nunique() == 2

def test_counterbalance_session_order_values():
    """Test that session_order only contains valid values"""
    df = generate_counterbalance_assignments(n_participants=100, seed=42, split_ratio=0.5)
    valid_orders = {'Low-High', 'High-Low'}
    assert set(df['session_order'].unique()).issubset(valid_orders)
