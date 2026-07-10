import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.counterbalance import generate_counterbalance_assignments
from utils.logging import get_log_path

def test_generate_counterbalance_even_split():
    """Test that even number of participants gets exact 50/50 split."""
    pids = [f"P{i}" for i in range(1, 11)]  # 10 participants
    df = generate_counterbalance_assignments(pids, seed=42)
    
    assert len(df) == 10
    assert set(df.columns) == {"participant_id", "session_order"}
    
    counts = df["session_order"].value_counts()
    assert counts["Low-High"] == 5
    assert counts["High-Low"] == 5

def test_generate_counterbalance_odd_split():
    """Test that odd number of participants gets +/- 1 split."""
    pids = [f"P{i}" for i in range(1, 11)]  # 10 participants
    # Add one more to make 11
    pids.append("P11")
    
    df = generate_counterbalance_assignments(pids, seed=42)
    
    assert len(df) == 11
    counts = df["session_order"].value_counts()
    
    # One group should be 6, the other 5
    assert counts.iloc[0] + counts.iloc[1] == 11
    assert abs(counts.iloc[0] - counts.iloc[1]) == 1

def test_counterbalance_deterministic():
    """Test that same seed produces same result."""
    pids = [f"P{i}" for i in range(1, 21)]
    df1 = generate_counterbalance_assignments(pids, seed=42)
    df2 = generate_counterbalance_assignments(pids, seed=42)
    
    pd.testing.assert_frame_equal(df1, df2)

def test_counterbalance_strategy_log_exists():
    """Test that the strategy log is created when main is run (simulated)."""
    # We can't easily run main() here without side effects, 
    # but we can verify the logging function exists and the path is correct.
    from utils.logging import log_counterbalance_strategy
    
    log_path = get_log_path()
    strategy_file = log_path / "counterbalance_strategy.log"
    
    # Ensure directory exists
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Write a dummy entry
    log_counterbalance_strategy("Test Strategy")
    
    assert strategy_file.exists()