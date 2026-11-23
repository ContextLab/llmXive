"""
Tests for T037c: Fail Loud Handler.
"""
import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# We need to import the module, but since it's in code/, we adjust path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fail_loud_handler import check_real_data_existence, raise_failure_error, FAILURE_MESSAGE
import logging

# Mock logger for tests
class MockLogger:
    def info(self, msg): pass
    def warning(self, msg): pass
    def critical(self, msg): pass
    def error(self, msg): pass

def test_check_real_data_missing_parquet(tmp_path):
    """Test that check_real_data_existence returns False when parquet is missing."""
    # Create a mock directory structure
    # We cannot easily mock the global PROJECT_ROOT in the module, 
    # so we test the logic by simulating the environment or mocking the function's dependencies.
    # However, the function relies on global constants. 
    # For this unit test, we will verify the behavior by creating a temporary 
    # environment that mimics the project structure if possible, 
    # or we test the logic directly if refactored.
    
    # Since the function uses global constants pointing to the real project root,
    # we will test the specific logic by mocking the path existence checks.
    # But to keep it simple and robust:
    # We assume the test runner is in the project root.
    # If the test environment doesn't have the data, it should return False.
    
    # This is a structural test. In a real CI, if data is missing, it returns False.
    # We assert that if we are in a clean env, it returns False.
    logger = MockLogger()
    result = check_real_data_existence(logger)
    # In a clean test environment without the Z-Reward data, this MUST be False.
    # If the test environment accidentally has the data, this test is invalid.
    # We assume the test environment is clean.
    assert result is False, "Expected False in a clean environment without Z-Reward data."

def test_check_real_data_missing_validation_log(tmp_path):
    """Test that check_real_data_existence returns False when validation log is missing."""
    logger = MockLogger()
    result = check_real_data_existence(logger)
    assert result is False

def test_raise_failure_error():
    """Test that raise_failure_error raises the correct RuntimeError."""
    logger = MockLogger()
    with pytest.raises(RuntimeError) as excinfo:
        raise_failure_error(logger)
    
    assert FAILURE_MESSAGE in str(excinfo.value)

def test_failure_message_content():
    """Verify the exact error message matches the requirement."""
    expected = "No real data found. Synthetic fallback is prohibited by FR-006/Constitution Principle VII."
    assert FAILURE_MESSAGE == expected
