"""
Unit tests for the derive_time_of_day module (Task T028d).
"""
import pytest
import pandas as pd
from datetime import datetime
from code.derive_time_of_day import categorize_hour, derive_time_of_day

def test_categorize_hour_morning():
    assert categorize_hour(5) == 'Morning'
    assert categorize_hour(11) == 'Morning'
    assert categorize_hour(6) == 'Morning'

def test_categorize_hour_afternoon():
    assert categorize_hour(12) == 'Afternoon'
    assert categorize_hour(16) == 'Afternoon'

def test_categorize_hour_evening():
    assert categorize_hour(17) == 'Evening'
    assert categorize_hour(20) == 'Evening'

def test_categorize_hour_night():
    assert categorize_hour(0) == 'Night'
    assert categorize_hour(4) == 'Night'
    assert categorize_hour(21) == 'Night'
    assert categorize_hour(23) == 'Night'

def test_derive_time_of_day_basic():
    data = {
        'participant_id': ['p1', 'p2', 'p3', 'p4'],
        'timestamp': [
            datetime(2016, 1, 1, 6, 0),
            datetime(2016, 1, 1, 14, 0),
            datetime(2016, 1, 1, 18, 0),
            datetime(2016, 1, 1, 23, 0)
        ]
    }
    df = pd.DataFrame(data)
    result = derive_time_of_day(df)
    
    assert 'time_of_day' in result.columns
    assert 'hour' in result.columns
    assert len(result) == 4
    
    assert result.iloc[0]['time_of_day'] == 'Morning'
    assert result.iloc[1]['time_of_day'] == 'Afternoon'
    assert result.iloc[2]['time_of_day'] == 'Evening'
    assert result.iloc[3]['time_of_day'] == 'Night'

def test_derive_time_of_day_missing_timestamp():
    data = {
        'participant_id': ['p1'],
        'response_time': [1000]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="Input DataFrame must contain a 'timestamp' column."):
        derive_time_of_day(df)
