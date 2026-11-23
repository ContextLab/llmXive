"""
Pytest-compatible integration test for T113.
"""
import pytest
import sys
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).resolve().parent.parent.parent / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from tests.test_collinearity_detection import test_collinearity_detection_integration

def test_collinearity_detection():
    """
    Assert that the collinearity detection test passes.
    """
    # Run the test function
    result = test_collinearity_detection_integration()
    assert result is True, "Collinearity detection test failed"