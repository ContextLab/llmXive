"""
Integration tests for the Pushshift log fetching functionality.

These tests verify that the fetch_pushshift.py script correctly:
1. Loads the survey window and matched users
2. Fetches logs within the specified time window
3. Handles rate limiting gracefully
4. Produces valid output files
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.ingest.fetch_pushshift import (
    load_survey_window,
    load_matched_users,
    fetch_pushshift_logs_for_user,
    fetch_all_pushshift_logs
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_window_file(temp_dir):
    """Create a sample survey window JSON file."""
    window_data = {
        "start_date": "2023-01-01T00:00:00",
        "end_date": "2023-12-31T23:59:59"
    }
    window_path = temp_dir / "survey_window_final.json"
    with open(window_path, 'w') as f:
        json.dump(window_data, f)
    return window_path


@pytest.fixture
def sample_matched_users_file(temp_dir):
    """Create a sample matched users parquet file."""
    users_data = {
        "user_id": ["user_001", "user_002", "user_003"],
        "username_hash": ["hash123", "hash456", "hash789"],
        "loneliness_score": [2.5, 3.1, 4.0]
    }
    users_df = pd.DataFrame(users_data)
    users_path = temp_dir / "matched_users.parquet"
    users_df.to_parquet(users_path)
    return users_path


def test_load_survey_window_valid(sample_window_file):
    """Test loading a valid survey window file."""
    window = load_survey_window(sample_window_file)
    
    assert 'start_date' in window
    assert 'end_date' in window
    assert isinstance(window['start_date'], datetime)
    assert isinstance(window['end_date'], datetime)
    assert window['start_date'] < window['end_date']


def test_load_survey_window_missing_file(temp_dir):
    """Test that loading a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_survey_window(temp_dir / "nonexistent.json")


def test_load_survey_window_invalid_format(temp_dir):
    """Test that loading a file with invalid format raises an error."""
    invalid_path = temp_dir / "invalid.json"
    with open(invalid_path, 'w') as f:
        json.dump({"wrong_key": "value"}, f)
    
    with pytest.raises(ValueError):
        load_survey_window(invalid_path)


def test_load_matched_users_valid(sample_matched_users_file):
    """Test loading a valid matched users file."""
    users = load_matched_users(sample_matched_users_file)
    
    assert 'user_id' in users.columns
    assert 'username_hash' in users.columns
    assert len(users) == 3


def test_load_matched_users_missing_columns(temp_dir):
    """Test that loading a file with missing columns raises an error."""
    bad_data = {"user_id": ["user_001"]}
    bad_df = pd.DataFrame(bad_data)
    bad_path = temp_dir / "bad.parquet"
    bad_df.to_parquet(bad_path)
    
    with pytest.raises(ValueError):
        load_matched_users(bad_path)


@patch('src.ingest.fetch_pushshift.fetch_pushshift_logs_for_user')
def test_fetch_all_pushshift_logs_with_mocked_api(
    mock_fetch_logs,
    sample_matched_users_file,
    sample_window_file,
    temp_dir
):
    """Test the full fetch pipeline with mocked API calls."""
    # Mock the API response
    mock_logs = [
        {
            "author": "hash123",
            "created_utc": 1672531200,
            "body": "Test comment",
            "subreddit": "Replika",
            "score": 5
        },
        {
            "author": "hash456",
            "created_utc": 1672617600,
            "body": "Another comment",
            "subreddit": "characterAI",
            "score": 3
        }
    ]
    
    # Configure mock to return different logs for different users
    def mock_side_effect(user_id, username_hash, start_date, end_date, subreddits):
        if username_hash == "hash123":
            return [mock_logs[0]]
        elif username_hash == "hash456":
            return [mock_logs[1]]
        else:
            return []
    
    mock_fetch_logs.side_effect = mock_side_effect
    
    output_path = temp_dir / "pushshift_logs_refined.parquet"
    
    # Run the fetch function
    fetch_all_pushshift_logs(
        sample_matched_users_file,
        sample_window_file,
        output_path
    )
    
    # Verify output was created
    assert output_path.exists()
    
    # Verify output content
    result_df = pd.read_parquet(output_path)
    assert len(result_df) == 2
    assert 'user_id' in result_df.columns
    assert 'created_utc' in result_df.columns


@patch('src.ingest.fetch_pushshift.requests.get')
def test_fetch_pushshift_logs_handles_rate_limit(mock_get, sample_matched_users_file, sample_window_file, temp_dir):
    """Test that rate limiting is handled gracefully."""
    from src.utils.rate_limit_handler import RateLimitError
    
    # Mock a rate limit response
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {'Retry-After': '60'}
    mock_get.return_value = mock_response
    
    output_path = temp_dir / "pushshift_logs_refined.parquet"
    
    # Should not raise an exception, but log a warning
    fetch_all_pushshift_logs(
        sample_matched_users_file,
        sample_window_file,
        output_path
    )
    
    # Output file should still be created (possibly empty)
    assert output_path.exists()