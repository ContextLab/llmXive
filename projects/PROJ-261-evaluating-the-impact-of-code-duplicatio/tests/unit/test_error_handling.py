import pytest
import math
import os
import csv
from pathlib import Path
import tempfile
import shutil

# Mock config for testing
import sys
from unittest.mock import patch, MagicMock

# We need to mock the config to point to a temp directory
@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def mock_config(temp_dir):
    with patch('error_handling.get_data_root', return_value=Path(temp_dir)):
        with patch('error_handling.get_raw_dir', return_value=Path(temp_dir)):
            with patch('error_handling.get_processed_dir', return_value=Path(temp_dir)):
                yield Path(temp_dir)

def test_log_parse_failure(mock_config):
    """Test that parse failures are logged to CSV."""
    from error_handling import log_parse_failure, get_parse_failures_path
    
    test_file = "test.py"
    error_type = "SyntaxError"
    error_msg = "Invalid syntax"
    
    log_parse_failure(test_file, error_type, error_msg)
    
    log_path = get_parse_failures_path()
    assert log_path.exists(), "Log file should be created"
    
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['error_type'] == error_type
        assert rows[0]['file_path'] == test_file

def test_handle_nan_perplexity(mock_config):
    """Test that NaN/Inf perplexity values are detected and logged."""
    from error_handling import handle_nan_perplexity, get_parse_failures_path
    import math
    
    test_file = "code.py"
    segment_id = "seg_001"
    
    # Test NaN
    result = handle_nan_perplexity(test_file, segment_id, float('nan'))
    assert result is None, "NaN should return None"
    
    # Test Inf
    result = handle_nan_perplexity(test_file, segment_id, float('inf'))
    assert result is None, "Inf should return None"
    
    # Test valid
    result = handle_nan_perplexity(test_file, segment_id, 5.0)
    assert result == 5.0, "Valid value should be returned"
    
    # Check log
    log_path = get_parse_failures_path()
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) >= 2 # At least the two error cases
        # Verify error types
        error_types = [r['error_type'] for r in rows]
        assert 'InvalidPerplexity' in error_types

def test_handle_network_interruption(mock_config):
    """Test network error handling logic."""
    from error_handling import handle_network_interruption
    import socket
    
    # Test retry logic
    error = socket.timeout("Timeout")
    
    # First attempt should retry
    should_retry = handle_network_interruption("Test Op", error, retry_count=0, max_retries=3)
    assert should_retry is True
    
    # Max retries should not retry
    should_retry = handle_network_interruption("Test Op", error, retry_count=3, max_retries=3)
    assert should_retry is False

def test_validate_perplexity_input(mock_config):
    """Test input validation."""
    from error_handling import validate_perplexity_input
    
    is_valid, msg = validate_perplexity_input(None)
    assert not is_valid
    
    is_valid, msg = validate_perplexity_input("10.5")
    assert is_valid
    
    is_valid, msg = validate_perplexity_input(float('nan'))
    assert not is_valid

def test_handle_parse_error(mock_config):
    """Test the centralized error handler."""
    from error_handling import handle_parse_error, get_parse_failures_path
    
    test_file = "broken.py"
    try:
        compile("def broken(", filename="test", mode="exec")
    except SyntaxError as e:
        handle_parse_error(test_file, e, "AST Parsing")
    
    log_path = get_parse_failures_path()
    assert log_path.exists()
    with open(log_path, 'r') as f:
        content = f.read()
        assert "SyntaxError" in content
