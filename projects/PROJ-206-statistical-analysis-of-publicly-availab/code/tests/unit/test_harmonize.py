import os
import sys
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from datetime import datetime, timedelta

# Import the function to test
# Adjust import path based on project structure (assuming code/ is root for imports)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from src.data.harmonize import check_data_sufficiency

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with valid dates and cycles."""
    data = {
        'date': pd.date_range(start='2024-10-01', periods=10, freq='D'),
        'pollster': ['P1'] * 10,
        'vote_share': [50.0] * 10,
        'sample_size': [1000] * 10,
        'cycle': [2024] * 10
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_df():
    """Create a larger DataFrame spanning multiple cycles."""
    dates_2024 = pd.date_range(start='2024-01-01', periods=300, freq='D')
    dates_2020 = pd.date_range(start='2020-01-01', periods=300, freq='D')
    dates_2016 = pd.date_range(start='2016-01-01', periods=300, freq='D')
    
    data_2024 = {
        'date': dates_2024,
        'pollster': ['P1'] * 300,
        'vote_share': [50.0] * 300,
        'sample_size': [1000] * 300,
        'cycle': [2024] * 300
    }
    data_2020 = {
        'date': dates_2020,
        'pollster': ['P1'] * 300,
        'vote_share': [50.0] * 300,
        'sample_size': [1000] * 300,
        'cycle': [2020] * 300
    }
    data_2016 = {
        'date': dates_2016,
        'pollster': ['P1'] * 300,
        'vote_share': [50.0] * 300,
        'sample_size': [1000] * 300,
        'cycle': [2016] * 300
    }
    
    df = pd.concat([pd.DataFrame(data_2024), pd.DataFrame(data_2020), pd.DataFrame(data_2016)], ignore_index=True)
    return df

def test_check_data_sufficiency_pass(sample_df):
    """Test that sufficient data returns True."""
    election_date = datetime(2024, 11, 5)
    # sample_df has 10 polls in Oct 2024, which is within 30 days of Nov 5, 2024
    # It has 1 cycle. We need to adjust the test to pass the cycle check or mock it.
    # Let's create a specific scenario for the pass case.
    
    # Create data with 5 polls in last 30 days and 3 cycles
    recent_dates = pd.date_range(start='2024-10-01', periods=10, freq='D')
    old_data = []
    for year in [2024, 2020, 2016]:
        old_data.append({
            'date': pd.date_range(start=f'{year}-01-01', periods=10, freq='D'),
            'pollster': ['P1']*10,
            'vote_share': [50.0]*10,
            'sample_size': [1000]*10,
            'cycle': [year]*10
        })
    
    full_df = pd.concat([pd.DataFrame({'date': recent_dates, 'pollster': ['P1']*10, 'vote_share': [50.0]*10, 'sample_size': [1000]*10, 'cycle': [2024]*10})] + [pd.DataFrame(d) for d in old_data], ignore_index=True)
    
    result = check_data_sufficiency(full_df, election_date)
    assert result is True

def test_check_data_sufficiency_fail_recent(sample_df):
    """Test that insufficient recent polls returns False."""
    # Create data with only 2 polls in the last 30 days
    election_date = datetime(2024, 11, 5)
    recent_dates = pd.date_range(start='2024-10-20', periods=2, freq='D') # Only 2 polls
    
    df = pd.DataFrame({
        'date': recent_dates,
        'pollster': ['P1'] * 2,
        'vote_share': [50.0] * 2,
        'sample_size': [1000] * 2,
        'cycle': [2024] * 2
    })
    
    # Add old data to satisfy cycle count but fail recent count
    for year in [2020, 2016]:
        old_dates = pd.date_range(start=f'{year}-01-01', periods=10, freq='D')
        old_df = pd.DataFrame({
            'date': old_dates,
            'pollster': ['P1'] * 10,
            'vote_share': [50.0] * 10,
            'sample_size': [1000] * 10,
            'cycle': [year] * 10
        })
        df = pd.concat([df, old_df], ignore_index=True)
    
    result = check_data_sufficiency(df, election_date)
    assert result is False

def test_check_data_sufficiency_fail_cycles(sample_df):
    """Test that insufficient cycles returns False."""
    election_date = datetime(2024, 11, 5)
    
    # Create data with enough recent polls but only 1 cycle
    recent_dates = pd.date_range(start='2024-10-01', periods=10, freq='D')
    df = pd.DataFrame({
        'date': recent_dates,
        'pollster': ['P1'] * 10,
        'vote_share': [50.0] * 10,
        'sample_size': [1000] * 10,
        'cycle': [2024] * 10
    })
    
    result = check_data_sufficiency(df, election_date)
    assert result is False

def test_check_data_sufficiency_fail_total(sample_df):
    """Test that empty dataframe returns False."""
    election_date = datetime(2024, 11, 5)
    df = pd.DataFrame(columns=['date', 'pollster', 'vote_share', 'sample_size', 'cycle'])
    
    result = check_data_sufficiency(df, election_date)
    assert result is False