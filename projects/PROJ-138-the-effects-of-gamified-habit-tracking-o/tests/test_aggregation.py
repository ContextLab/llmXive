"""
Tests for data aggregation logic.
"""
import pytest
import pandas as pd
from code.data.aggregation import aggregate_weekly

def test_weekly_aggregation():
    """
    Test that aggregation correctly generates week_number and weekly_adherence_flag.
    """
    # Create mock data
    data = {
        "user_id": ["U1", "U1", "U1", "U2", "U2"],
        "week_number": [1, 1, 2, 1, 1],
        "gamification_status": [True, True, True, False, False],
        "conscientiousness_score": [3.5, 3.5, 3.5, 4.0, 4.0],
        "adherence_flag": [1, 0, 1, 0, 0] # U1: W1=0.5->0, W2=1->1; U2: W1=0->0
    }
    df = pd.DataFrame(data)
    
    result = aggregate_weekly(df)
    
    # Check columns
    assert "weekly_adherence_flag" in result.columns
    assert "week_number" in result.columns
    
    # Check values
    # U1, W1: mean=0.5 -> flag=0 (since >0.5 is 1, 0.5 is not >0.5)
    # U1, W2: mean=1.0 -> flag=1
    # U2, W1: mean=0.0 -> flag=0
    
    u1_w1 = result[(result["user_id"] == "U1") & (result["week_number"] == 1)]
    assert len(u1_w1) == 1
    assert u1_w1["weekly_adherence_flag"].iloc[0] == 0
    
    u1_w2 = result[(result["user_id"] == "U1") & (result["week_number"] == 2)]
    assert len(u1_w2) == 1
    assert u1_w2["weekly_adherence_flag"].iloc[0] == 1
    
    u2_w1 = result[(result["user_id"] == "U2") & (result["week_number"] == 1)]
    assert len(u2_w1) == 1
    assert u2_w1["weekly_adherence_flag"].iloc[0] == 0