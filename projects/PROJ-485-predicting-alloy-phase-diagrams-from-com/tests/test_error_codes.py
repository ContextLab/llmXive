"""
Tests for the error_codes module.

This module verifies that the ErrorCode Enum is properly defined
and contains all required error codes with correct string values.
"""
import sys
import os
from enum import Enum

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.error_codes import ErrorCode


def test_error_codes_exist():
    """Verify all required error codes exist in the ErrorCode Enum."""
    required_codes = [
        'DATA_SOURCE_MISSING',
        'INVALID_DATA_SCHEMA',
        'MISSING_TEMP_COORDS',
        'LOW_DATA_DENSITY',
        'API_RATE_LIMIT_EXCEEDED',
        'INSUFFICIENT_POWER'
    ]
    
    for code_name in required_codes:
        assert hasattr(ErrorCode, code_name), f"Missing error code: {code_name}"
        
        # Verify the value is a string
        code_value = getattr(ErrorCode, code_name).value
        assert isinstance(code_value, str), f"Error code {code_name} value is not a string"
        
        # Verify the value matches the name (convention)
        assert code_value == code_name, f"Error code {code_name} value mismatch: {code_value} != {code_name}"


def test_error_code_usage():
    """Verify error codes can be used as expected in error handling."""
    # Test direct access
    assert ErrorCode.DATA_SOURCE_MISSING.value == "DATA_SOURCE_MISSING"
    assert ErrorCode.INVALID_DATA_SCHEMA.value == "INVALID_DATA_SCHEMA"
    assert ErrorCode.MISSING_TEMP_COORDS.value == "MISSING_TEMP_COORDS"
    assert ErrorCode.LOW_DATA_DENSITY.value == "LOW_DATA_DENSITY"
    assert ErrorCode.API_RATE_LIMIT_EXCEEDED.value == "API_RATE_LIMIT_EXCEEDED"
    assert ErrorCode.INSUFFICIENT_POWER.value == "INSUFFICIENT_POWER"
    
    # Test iteration
    code_list = list(ErrorCode)
    assert len(code_list) == 6, f"Expected 6 error codes, got {len(code_list)}"
    
    # Test string conversion
    for code in ErrorCode:
        assert isinstance(str(code), str)
        assert isinstance(code.name, str)
        assert isinstance(code.value, str)


def test_error_code_comparison():
    """Verify error codes can be compared correctly."""
    assert ErrorCode.DATA_SOURCE_MISSING == ErrorCode.DATA_SOURCE_MISSING
    assert ErrorCode.INVALID_DATA_SCHEMA != ErrorCode.DATA_SOURCE_MISSING
    
    # Test value comparison
    assert ErrorCode.DATA_SOURCE_MISSING.value == "DATA_SOURCE_MISSING"
    assert ErrorCode.DATA_SOURCE_MISSING.value != "OTHER_ERROR"


if __name__ == "__main__":
    test_error_codes_exist()
    test_error_code_usage()
    test_error_code_comparison()
    print("All error code tests passed.")