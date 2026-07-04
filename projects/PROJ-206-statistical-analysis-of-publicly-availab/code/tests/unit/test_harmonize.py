import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from datetime import timedelta
import logging

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.harmonize import check_data_sufficiency, harmonize_data, parse_raw_csvs

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def sample_raw_data(tmp_path):
    """Create a temporary CSV file with sample poll data."""
    data = {
        'pollster': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        'date': [
            '2024-10-01', '2024-10-05', '2024-10-10', '2024-10-15', '2024-10-20',
            '2024-10-25', '2024-10-28', '2024-11-01', '2024-11-03', '2024-11-04'
        ],
        'vote_share': [45.0, 46.0, 45.5, 47.0, 46.5, 48.0, 47.5, 49.0, 48.5, 49.5],
        'sample_size': [1000, 1200, 1100, 1300, 1150, 1400, 1250, 1500, 1350, 1600],
        'cycle': [2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "polls.csv"
    df.to_csv(file_path, index=False)
    return tmp_path, df

@pytest.fixture
def insufficient_recent_data(tmp_path):
    """Create data with insufficient polls in the 30-day window."""
    data = {
        'pollster': ['A', 'B'],
        'date': ['2024-09-01', '2024-09-15'],
        'vote_share': [45.0, 46.0],
        'sample_size': [1000, 1200],
        'cycle': [2024, 2024]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "polls.csv"
    df.to_csv(file_path, index=False)
    return tmp_path, df

@pytest.fixture
def insufficient_cycles(tmp_path):
    """Create data with only 2 distinct cycles."""
    data = {
        'pollster': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        'date': [
            '2024-10-01', '2024-10-05', '2024-10-10', '2024-10-15', '2024-10-20',
            '2024-10-25', '2024-10-28', '2024-11-01', '2024-11-03', '2024-11-04'
        ],
        'vote_share': [45.0, 46.0, 45.5, 47.0, 46.5, 48.0, 47.5, 49.0, 48.5, 49.5],
        'sample_size': [1000, 1200, 1100, 1300, 1150, 1400, 1250, 1500, 1350, 1600],
        'cycle': [2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024, 2024] # Only 1 cycle here, need to adjust for 2
    }
    # Let's make it 2 cycles
    data['cycle'] = [2024, 2024, 2024, 2024, 2024, 2020, 2020, 2020, 2020, 2020]
    df = pd.DataFrame(data)
    file_path = tmp_path / "polls.csv"
    df.to_csv(file_path, index=False)
    return tmp_path, df

def test_check_data_sufficiency_pass(sample_raw_data):
    """Test that sufficient data passes the check."""
    _, df = sample_raw_data
    election_date = pd.Timestamp("2024-11-05")
    is_sufficient, msg = check_data_sufficiency(df, election_date)
    assert is_sufficient is True
    assert "passed" in msg.lower()

def test_check_data_sufficiency_fail_recent(insufficient_recent_data):
    """Test that insufficient recent data fails the check."""
    _, df = insufficient_recent_data
    election_date = pd.Timestamp("2024-10-01") # Window starts 2024-09-01, only 2 polls
    is_sufficient, msg = check_data_sufficiency(df, election_date)
    assert is_sufficient is False
    assert "failed" in msg.lower()
    assert "polls" in msg.lower()

def test_check_data_sufficiency_fail_cycles(insufficient_cycles):
    """Test that insufficient cycles fails the check."""
    _, df = insufficient_cycles
    election_date = pd.Timestamp("2024-11-05")
    # The data has 2 cycles (2024, 2020), which is < 3
    is_sufficient, msg = check_data_sufficiency(df, election_date)
    assert is_sufficient is False
    assert "failed" in msg.lower()
    assert "cycles" in msg.lower()

def test_harmonize_data_integration(sample_raw_data):
    """Test the full harmonize_data function with sufficient data."""
    raw_dir, _ = sample_raw_data
    election_date = pd.Timestamp("2024-11-05")
    
    # This should not raise an error
    df = harmonize_data(raw_dir, election_date)
    assert not df.empty
    assert 'week_start' in df.columns
    assert 'date' in df.columns

def test_harmonize_data_integration_fail(insufficient_recent_data):
    """Test that harmonize_data raises an error with insufficient data."""
    raw_dir, _ = insufficient_recent_data
    election_date = pd.Timestamp("2024-10-01")
    
    with pytest.raises(ValueError):
        harmonize_data(raw_dir, election_date)
