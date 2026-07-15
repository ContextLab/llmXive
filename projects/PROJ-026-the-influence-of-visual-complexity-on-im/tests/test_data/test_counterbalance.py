import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.counterbalance import generate_counterbalance_assignments

def test_generate_counterbalance_assignments_seed():
    """Test that the same seed produces the same results."""
    df1 = generate_counterbalance_assignments(n_participants=10, seed=42)
    df2 = generate_counterbalance_assignments(n_participants=10, seed=42)
    
    pd.testing.assert_frame_equal(df1, df2)

def test_generate_counterbalance_assignments_split():
    """Test that the split is approximately 50/50."""
    n = 1000
    df = generate_counterbalance_assignments(n_participants=n, seed=42)
    
    low_high = (df['session_order'] == "Low-High").sum()
    high_low = (df['session_order'] == "High-Low").sum()
    
    # With 1000, we expect exactly 500/500 due to integer division logic
    # (half = 1000 // 2 = 500, remaining = 500)
    assert low_high == high_low == 500

def test_generate_counterbalance_assignments_columns():
    """Test that the output has the correct columns."""
    df = generate_counterbalance_assignments(n_participants=5, seed=42)
    
    assert 'participant_id' in df.columns
    assert 'session_order' in df.columns
    assert len(df.columns) == 2

def test_generate_counterbalance_assignments_participant_ids():
    """Test that participant IDs are formatted correctly."""
    df = generate_counterbalance_assignments(n_participants=5, seed=42)
    
    expected_ids = ['P0001', 'P0002', 'P0003', 'P0004', 'P0005']
    assert list(df['participant_id']) == expected_ids

def test_generate_counterbalance_assignments_valid_orders():
    """Test that only valid session orders are generated."""
    df = generate_counterbalance_assignments(n_participants=100, seed=42)
    
    valid_orders = {"Low-High", "High-Low"}
    assert set(df['session_order'].unique()).issubset(valid_orders)