"""
Unit tests for consent logging functionality, specifically verifying
that IRB_PROTOCOL_ID is captured in the log.
"""
import os
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.helpers import log_consent_decision, get_consent_log_path
from utils.config import ENV_VAR_NAME

@pytest.fixture
def mock_env_and_dirs():
    """Sets up a temporary directory for testing and mocks the env var."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Mock the project root to be our temp dir
        with patch('utils.config.get_project_root', return_value=tmp_path):
            # Ensure consent directory exists
            (tmp_path / "data" / "consent").mkdir(parents=True, exist_ok=True)
            
            # Set the environment variable
            original_val = os.environ.get(ENV_VAR_NAME)
            os.environ[ENV_VAR_NAME] = "TEST-PROTOCOL-ID-999"
            
            yield tmp_path
            
            # Restore environment
            if original_val is None:
                os.environ.pop(ENV_VAR_NAME, None)
            else:
                os.environ[ENV_VAR_NAME] = original_val

def test_log_consent_includes_protocol_id(mock_env_and_dirs):
    """
    Test that log_consent_decision writes the IRB_PROTOCOL_ID to the CSV.
    """
    user_id = "user-123"
    decision = "agreed"
    
    # Call the function
    log_consent_decision(user_id, decision)
    
    # Verify file exists
    log_path = mock_env_and_dirs / "data" / "consent" / "consent_log.csv"
    assert log_path.exists(), "Consent log file should be created."
    
    # Read the file
    with open(log_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Verify row count
    assert len(rows) == 1, "Should have exactly one row."
    
    row = rows[0]
    
    # Verify columns
    assert 'timestamp' in row
    assert 'user_id' in row
    assert 'decision' in row
    assert 'irb_protocol_id' in row, "CSV must include 'irb_protocol_id' column."
    
    # Verify values
    assert row['user_id'] == user_id
    assert row['decision'] == decision
    assert row['irb_protocol_id'] == "TEST-PROTOCOL-ID-999", \
        f"Protocol ID in log must match environment variable. Got: {row['irb_protocol_id']}"

def test_log_consent_fails_without_env_var():
    """
    Test that log_consent_decision raises RuntimeError if IRB_PROTOCOL_ID is missing.
    """
    # Temporarily remove the env var
    original_val = os.environ.pop(ENV_VAR_NAME, None)
    
    try:
        with pytest.raises(RuntimeError) as exc_info:
            log_consent_decision("user-456", "agreed")
        
        assert ENV_VAR_NAME in str(exc_info.value)
    finally:
        # Restore
        if original_val:
            os.environ[ENV_VAR_NAME] = original_val
