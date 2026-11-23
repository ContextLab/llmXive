"""
Example unit test to verify pytest framework is working.
This test should pass and confirms the setup is correct.
"""
import pytest

def test_pytest_framework_available():
    """Verify that pytest is available and running."""
    assert pytest is not None

def test_basic_arithmetic():
    """Simple arithmetic test to ensure test execution works."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5

def test_string_operations():
    """Test string operations."""
    s = "polymer"
    assert s.upper() == "POLYMER"
    assert "poly" in s
