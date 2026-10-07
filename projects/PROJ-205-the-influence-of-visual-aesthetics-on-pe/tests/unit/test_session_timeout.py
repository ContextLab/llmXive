"""
Unit tests for Session Timeout and Abandonment Tracking (T071).
"""
import os
import sys
import time
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.survey.app import (
    check_session_timeout,
    log_abandonment,
    SESSION_TIMEOUT_MINUTES,
    ABANDONMENT_LOG_PATH
)

# Mock streamlit session state
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    def __setattr__(self, key, value):
        self[key] = value

@pytest.fixture
def mock_session_state():
    state = MockSessionState()
    state.participant_id = "test-participant-123"
    state.last_activity_time = time.time()
    return state

@pytest.fixture
def mock_st_session_state(mock_session_state):
    with patch('code.survey.app.st.session_state', mock_session_state):
        yield mock_session_state

def test_session_not_timeout(mock_st_session_state):
    """Test that a recent session does not timeout."""
    # Set last activity to now
    mock_st_session_state.last_activity_time = time.time()
    
    with patch('code.survey.app.time.time', return_value=time.time()):
        result = check_session_timeout()
        assert result is False

def test_session_timeout(mock_st_session_state):
    """Test that an old session times out."""
    # Set last activity to 31 minutes ago (assuming default 30 min timeout)
    old_time = time.time() - (31 * 60)
    mock_st_session_state.last_activity_time = old_time
    
    with patch('code.survey.app.time.time', return_value=time.time()):
        result = check_session_timeout()
        assert result is True
        # Verify state was updated (reset)
        assert mock_st_session_state.last_activity_time == time.time()

def test_log_abandonment_creates_file(mock_st_session_state, tmp_path):
    """Test that log_abandonment creates the correct CSV entry."""
    # Mock the log path to a temp directory
    temp_log = tmp_path / "abandonment_log.csv"
    
    with patch('code.survey.app.ABANDONMENT_LOG_PATH', temp_log):
        with patch('code.survey.app.get_irb_protocol_id', return_value="IRB-TEST-001"):
            log_abandonment("test-participant-123")
    
    # Verify file exists
    assert temp_log.exists()
    
    # Verify content
    with open(temp_log, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        assert row['participant_id'] == "test-participant-123"
        assert row['reason'] == 'session_timeout'
        assert 'IRB_PROTOCOL_ID' in row
        assert row['IRB_PROTOCOL_ID'] == "IRB-TEST-001"
        assert 'timestamp' in row

def test_log_abandonment_appends(mock_st_session_state, tmp_path):
    """Test that log_abandonment appends to existing log."""
    temp_log = tmp_path / "abandonment_log.csv"
    
    # Create initial file with header
    temp_log.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_log, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['participant_id', 'timestamp', 'reason', 'IRB_PROTOCOL_ID'])
        writer.writeheader()
        writer.writerow({'participant_id': 'old-id', 'timestamp': '2023-01-01', 'reason': 'timeout', 'IRB_PROTOCOL_ID': 'IRB-TEST-001'})
    
    with patch('code.survey.app.ABANDONMENT_LOG_PATH', temp_log):
        with patch('code.survey.app.get_irb_protocol_id', return_value="IRB-TEST-002"):
            log_abandonment("test-participant-123")
    
    with open(temp_log, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1]['participant_id'] == 'test-participant-123'
        assert rows[1]['IRB_PROTOCOL_ID'] == 'IRB-TEST-002'