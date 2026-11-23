"""
Unit tests for T025a: identify_contaminated_windows logic.
"""
import pytest
import pandas as pd
import numpy as np
from code.identify_contaminated_windows import identify_contaminated_segments


def test_no_contamination():
    """Test when G(t) never stays above median for > 20 steps."""
    # Create a simple dataset with 50 steps
    seed_id = "seed_001"
    timesteps = list(range(50))
    # Values oscillating around median
    values = [10.0 if i % 2 == 0 else 5.0 for i in range(50)]
    
    df = pd.DataFrame({
        "seed_id": [seed_id] * 50,
        "timestep": timesteps,
        "G_t": values
    })
    
    result = identify_contaminated_segments(df, window_size=20)
    
    # Median is 7.5. Values > 7.5 are 10.0.
    # They appear every other step, so no contiguous run > 20.
    assert result["is_contaminated"].sum() == 0


def test_contamination_detected():
    """Test when G(t) stays above median for > 20 steps."""
    seed_id = "seed_001"
    timesteps = list(range(50))
    # First 30 steps are high (10.0), next 20 are low (5.0)
    # Median will be 7.5. High > Median.
    values = [10.0] * 30 + [5.0] * 20
    
    df = pd.DataFrame({
        "seed_id": [seed_id] * 50,
        "timestep": timesteps,
        "G_t": values
    })
    
    result = identify_contaminated_segments(df, window_size=20)
    
    # The first 30 steps are > median. Duration 30 > 20.
    # So indices 0 to 29 should be True.
    assert result.loc[0:29, "is_contaminated"].all()
    assert not result.loc[30:49, "is_contaminated"].any()


def test_multiple_seeds():
    """Test contamination detection across multiple seeds."""
    data = []
    # Seed 1: Contaminated
    for i in range(50):
        data.append({
            "seed_id": "seed_1",
            "timestep": i,
            "G_t": 10.0 if i < 30 else 5.0
        })
    # Seed 2: Clean
    for i in range(50):
        data.append({
            "seed_id": "seed_2",
            "timestep": i,
            "G_t": 10.0 if i % 2 == 0 else 5.0
        })
    
    df = pd.DataFrame(data)
    result = identify_contaminated_segments(df, window_size=20)
    
    # Seed 1 should have contamination
    seed_1_mask = result[result["seed_id"] == "seed_1"]["is_contaminated"]
    assert seed_1_mask.sum() > 0
    
    # Seed 2 should have no contamination
    seed_2_mask = result[result["seed_id"] == "seed_2"]["is_contaminated"]
    assert seed_2_mask.sum() == 0


def test_boundary_duration():
    """Test exactly at the boundary (duration == window_size)."""
    seed_id = "seed_001"
    timesteps = list(range(30))
    # 20 steps high, 10 steps low. Window size 20.
    # Condition: duration > window_size. So 20 is NOT > 20.
    values = [10.0] * 20 + [5.0] * 10
    
    df = pd.DataFrame({
        "seed_id": [seed_id] * 30,
        "timestep": timesteps,
        "G_t": values
    })
    
    result = identify_contaminated_segments(df, window_size=20)
    
    # Duration is exactly 20, which is not > 20. No contamination.
    assert result["is_contaminated"].sum() == 0


def test_boundary_duration_plus_one():
    """Test just above boundary (duration == window_size + 1)."""
    seed_id = "seed_001"
    timesteps = list(range(31))
    # 21 steps high. Window size 20.
    values = [10.0] * 21 + [5.0] * 10
    
    df = pd.DataFrame({
        "seed_id": [seed_id] * 31,
        "timestep": timesteps,
        "G_t": values
    })
    
    result = identify_contaminated_segments(df, window_size=20)
    
    # Duration is 21, which is > 20. Contamination expected.
    assert result["is_contaminated"].sum() == 21