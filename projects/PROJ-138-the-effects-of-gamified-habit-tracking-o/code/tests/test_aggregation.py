import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from code.data.aggregation import aggregate_weekly

def test_weekly_aggregation():
    """
    Integration test: Assert the aggregation script correctly generates 
    `week_number` and `weekly_adherence_flag` columns from raw daily logs.
    
    This is a TDD Red task; previously the script did not exist.
    """
    # Arrange: Create a synthetic raw dataset with daily logs
    # Simulate 2 users, 14 days of data each
    user_ids = ['user_001'] * 14 + ['user_002'] * 14
    dates = []
    start_date = datetime(2023, 1, 1)
    for i in range(28):
        dates.append(start_date + timedelta(days=i % 14))
    
    # Create adherence data: 
    # user_001: Adherent days 1-7 (Week 1), Non-adherent 8-14 (Week 2)
    # user_002: Adherent days 1-3, Non-adherent 4-7, Adherent 8-14
    adherence_values = [1]*7 + [0]*7 + [1,1,1,0,0,0,0, 1,1,1,1,1,1,1]
    
    gamified_status = [True]*14 + [False]*14
    conscientiousness = [2.5]*14 + [3.8]*14
    
    raw_df = pd.DataFrame({
        'user_id': user_ids,
        'date': dates,
        'adherence_flag': adherence_values,
        'gamification_status': gamified_status,
        'conscientiousness_score': conscientiousness
    })
    
    # Act: Run the aggregation function
    aggregated_df = aggregate_weekly(raw_df)
    
    # Assert: Check structure and content
    assert 'week_number' in aggregated_df.columns, "Missing week_number column"
    assert 'weekly_adherence_flag' in aggregated_df.columns, "Missing weekly_adherence_flag column"
    assert 'user_id' in aggregated_df.columns, "Missing user_id column"
    
    # Verify week_number logic (should be sequential integers starting at 1)
    assert aggregated_df['week_number'].min() >= 1, "Week numbers must start at 1"
    assert aggregated_df['week_number'].is_monotonic_increasing or \
           aggregated_df['week_number'].nunique() == 2, "Week numbers should be sequential per user"
    
    # Verify weekly_adherence_flag logic (binary 0/1)
    assert aggregated_df['weekly_adherence_flag'].isin([0, 1]).all(), "Weekly adherence must be binary"
    
    # Verify specific aggregation logic for user_001
    # Week 1 should be 1 (all 1s), Week 2 should be 0 (all 0s)
    user_001_week1 = aggregated_df[(aggregated_df['user_id'] == 'user_001') & (aggregated_df['week_number'] == 1)]
    user_001_week2 = aggregated_df[(aggregated_df['user_id'] == 'user_001') & (aggregated_df['week_number'] == 2)]
    
    assert len(user_001_week1) == 1, "Should have exactly one row for user_001 week 1"
    assert len(user_001_week2) == 1, "Should have exactly one row for user_001 week 2"
    assert user_001_week1['weekly_adherence_flag'].iloc[0] == 1, "Week 1 adherence should be 1"
    assert user_001_week2['weekly_adherence_flag'].iloc[0] == 0, "Week 2 adherence should be 0"
    
    # Verify specific aggregation logic for user_002
    # Week 1: 3 ones, 4 zeros -> avg < 0.5 -> 0
    # Week 2: 7 ones -> avg >= 0.5 -> 1
    user_002_week1 = aggregated_df[(aggregated_df['user_id'] == 'user_002') & (aggregated_df['week_number'] == 1)]
    user_002_week2 = aggregated_df[(aggregated_df['user_id'] == 'user_002') & (aggregated_df['week_number'] == 2)]
    
    assert len(user_002_week1) == 1, "Should have exactly one row for user_002 week 1"
    assert len(user_002_week2) == 1, "Should have exactly one row for user_002 week 2"
    assert user_002_week1['weekly_adherence_flag'].iloc[0] == 0, "Week 1 adherence should be 0 (3/7 < 0.5)"
    assert user_002_week2['weekly_adherence_flag'].iloc[0] == 1, "Week 2 adherence should be 1 (7/7 >= 0.5)"