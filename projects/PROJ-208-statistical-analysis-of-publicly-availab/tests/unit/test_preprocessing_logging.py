"""
Unit tests for preprocessing logging functionality (Task T012).
Verifies that excluded issues are logged correctly in JSON format.
"""
import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from collect.preprocess import parse_timestamp, compute_resolution_time, is_valid_issue, preprocess_issues
from collect.setup_preprocessing_logging import setup_preprocessing_logging

def test_parse_timestamp_valid():
    """Test parsing valid ISO 8601 timestamps."""
    ts_str = "2023-01-01T12:00:00Z"
    dt = parse_timestamp(ts_str)
    assert dt is not None
    assert dt.year == 2023
    assert dt.month == 1
    assert dt.day == 1

def test_parse_timestamp_none():
    """Test parsing None/NaN timestamps."""
    assert parse_timestamp(None) is None
    assert parse_timestamp("") is None

def test_compute_resolution_time():
    """Test resolution time calculation."""
    start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    hours = compute_resolution_time(start, end)
    assert hours == 10.0

def test_is_valid_issue_negative_time_logs():
    """Test that negative resolution time triggers a log entry."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_path = Path(f.name)
    
    logger = setup_preprocessing_logging(log_path)
    
    # Issue with closed_at before created_at
    issue = {
        'id': 123,
        'repository': 'test-repo',
        'created_at': '2023-01-02T12:00:00Z',
        'closed_at': '2023-01-01T12:00:00Z'
    }
    
    is_valid, reason = is_valid_issue(issue, logger)
    
    assert not is_valid
    assert "Negative" in reason
    
    # Verify log file content
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    log_entry = json.loads(log_content.strip())
    assert log_entry['level'] == 'WARNING'
    assert 'Negative resolution time' in log_entry['message']
    assert log_entry['issue_id'] == 123
    assert log_entry['reason'] == reason

def test_is_valid_issue_missing_created_at_logs():
    """Test that missing created_at triggers a log entry."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_path = Path(f.name)
    
    logger = setup_preprocessing_logging(log_path)
    
    issue = {
        'id': 456,
        'repository': 'test-repo',
        'created_at': None,
        'closed_at': '2023-01-01T12:00:00Z'
    }
    
    is_valid, reason = is_valid_issue(issue, logger)
    
    assert not is_valid
    assert "created_at" in reason
    
    with open(log_path, 'r') as f:
        log_content = f.read()
    
    log_entry = json.loads(log_content.strip())
    assert log_entry['level'] == 'WARNING'
    assert "created_at" in log_entry['message']

def test_preprocess_issues_logs_all_exclusions():
    """Test that preprocess_issues logs all excluded issues."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        log_path = Path(f.name)
    
    logger = setup_preprocessing_logging(log_path)
    
    issues = [
        {
            'id': 1,
            'repository': 'repo-a',
            'created_at': '2023-01-01T00:00:00Z',
            'closed_at': '2023-01-01T01:00:00Z' # Valid
        },
        {
            'id': 2,
            'repository': 'repo-a',
            'created_at': None, # Invalid
            'closed_at': '2023-01-01T01:00:00Z'
        },
        {
            'id': 3,
            'repository': 'repo-a',
            'created_at': '2023-01-02T00:00:00Z',
            'closed_at': '2023-01-01T00:00:00Z' # Negative
        }
    ]
    
    valid_issues = preprocess_issues(issues, log_path)
    
    assert len(valid_issues) == 1
    assert valid_issues[0]['id'] == 1
    
    # Verify log file has 2 entries (for id 2 and 3)
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    # Filter for WARNING level
    warning_logs = [json.loads(line) for line in lines if '"WARNING"' in line]
    assert len(warning_logs) == 2
    
    ids_logged = [log['issue_id'] for log in warning_logs]
    assert 2 in ids_logged
    assert 3 in ids_logged