import os
import json
import tempfile
import pytest
import logging
from datetime import datetime

# Mock the main module's dependencies to test the function in isolation
# We need to test log_data_quality_warnings specifically

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.main import log_data_quality_warnings

@pytest.fixture
def temp_quality_log():
    """Create a temporary quality log file for testing."""
    # Create a temp file path
    temp_dir = tempfile.mkdtemp()
    log_path = os.path.join(temp_dir, "quality_log.json")
    
    # Initialize empty log
    with open(log_path, 'w') as f:
        json.dump([], f)
    
    yield log_path
    
    # Cleanup
    if os.path.exists(log_path):
        os.remove(log_path)
    os.rmdir(temp_dir)

def test_quality_log_schema(temp_quality_log):
    """
    Test that log_data_quality_warnings writes entries with the correct schema.
    Verifies FR-009 and T016 requirements.
    """
    # Prepare test warnings
    warnings = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "WARN",
            "source": "test_source",
            "message": "Test warning message"
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "source": "test_source",
            "message": "Test error message"
        }
    ]
    
    # Mock logger to avoid console spam
    mock_logger = logging.getLogger("test_logger")
    
    # Call the function with the temp path
    # We need to monkeypatch the constant in the module or pass the path
    # Since the function uses a global constant, we will test by calling it and checking the file
    # But the function uses a hardcoded path. We need to modify the test to work with the actual implementation.
    # The implementation writes to "data/processed/quality_log.json".
    # For unit testing, we should ideally refactor to accept a path, but per task constraints we test the current implementation.
    # We will create the directory structure expected by the function.
    
    os.makedirs("data/processed", exist_ok=True)
    initial_log_path = "data/processed/quality_log.json"
    
    # Ensure file exists and is empty
    with open(initial_log_path, 'w') as f:
        json.dump([], f)
    
    try:
        log_data_quality_warnings(warnings, mock_logger)
        
        # Verify file exists
        assert os.path.exists(initial_log_path), "Quality log file was not created."
        
        # Load and verify content
        with open(initial_log_path, 'r') as f:
            log_content = json.load(f)
        
        assert isinstance(log_content, list), "Log content must be a list."
        assert len(log_content) == 2, f"Expected 2 entries, found {len(log_content)}"
        
        # Verify schema for each entry
        required_keys = {'timestamp', 'level', 'source', 'message'}
        for entry in log_content:
            assert isinstance(entry, dict), "Each entry must be a dictionary."
            assert required_keys.issubset(entry.keys()), f"Entry missing required keys: {required_keys - set(entry.keys())}"
            assert entry['level'] in ['WARN', 'ERROR'], f"Invalid level: {entry['level']}"
            assert isinstance(entry['timestamp'], str), "Timestamp must be a string."
            assert isinstance(entry['message'], str), "Message must be a string."
            assert isinstance(entry['source'], str), "Source must be a string."
        
        # Verify specific content
        assert log_content[0]['source'] == 'test_source'
        assert log_content[0]['level'] == 'WARN'
        assert log_content[1]['level'] == 'ERROR'
        
    finally:
        # Cleanup
        if os.path.exists(initial_log_path):
            os.remove(initial_log_path)
        if os.path.exists("data/processed"):
            os.rmdir("data/processed")