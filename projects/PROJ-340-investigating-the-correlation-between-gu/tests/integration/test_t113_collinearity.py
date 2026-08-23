"""
pytest wrapper for T113 Collinearity Detection Integration Test.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from tests.test_collinearity_detection import test_collinearity_detection_integration


def test_halt_on_perfect_collinearity():
    """
    Pytest wrapper for the T113 integration test.
    Asserts that the system correctly identifies perfect multicollinearity
    and handles VIF skipping.
    """
    # This will raise an AssertionError if the test fails internally
    test_collinearity_detection_integration()
