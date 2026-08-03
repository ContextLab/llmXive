import os
import sys
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from src.data.harmonize import check_global_poll_count

@pytest.fixture
def sample_df():
    """Create a small dataframe with < 500 rows for testing failure."""
    data = {
        'date': pd.date_range(start='2020-01-01', periods=100),
        'pollster': ['A'] * 100,
        'vote_share': [0.5] * 100,
        'sample_size': [1000] * 100,
        'election_year': [2020] * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def large_df():
    """Create a dataframe with > 500 rows for testing success."""
    n = 600
    data = {
        'date': pd.date_range(start='2020-01-01', periods=n),
        'pollster': ['A'] * n,
        'vote_share': [0.5] * n,
        'sample_size': [1000] * n,
        'election_year': [2020] * n
    }
    return pd.DataFrame(data)

def test_check_global_poll_count_fail(sample_df):
    """Test that the function raises ValueError when count < 500."""
    with pytest.raises(ValueError) as excinfo:
        check_global_poll_count(sample_df)
    assert "Global poll count check failed" in str(excinfo.value)
    assert "500" in str(excinfo.value)

def test_check_global_poll_count_pass(large_df):
    """Test that the function returns silently when count >= 500."""
    # Should not raise
    result = check_global_poll_count(large_df)
    assert result is None