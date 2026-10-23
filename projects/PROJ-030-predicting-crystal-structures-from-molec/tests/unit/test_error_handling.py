"""
Unit tests for the error handling utilities.

The original task T007 expects a test that imports the module as
``from utils.error_handlers import …``.  Because the module lives under
``code/utils/error_handlers.py`` we need to adjust the import path so that
the test can be collected by pytest.  The test simply verifies that a
``MemoryError`` raised inside a wrapped function is re‑raised as the custom
``MemoryErrorHandled`` exception.
"""

import sys
from pathlib import Path

# Ensure the project root is on ``sys.path`` so that the ``code`` package can be imported.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import the custom exception types from the project's ``exceptions`` module.
from exceptions import MemoryErrorHandled

# Import the decorator from the actual location.
from code.utils.error_handlers import handle_memory_error

def function_raising_memory_error():
    raise MemoryError("simulated memory exhaustion")

@handle_memory_error
def wrapped_function():
    return function_raising_memory_error()

def test_catches_memory_error():
    """
    The wrapped function should raise ``MemoryErrorHandled`` and not the raw
    ``MemoryError``.
    """
    try:
        wrapped_function()
    except MemoryErrorHandled as e:
        # The test passes if the custom exception is raised.
        assert "MemoryErrorHandled" in str(type(e))
    else:
        raise AssertionError("MemoryErrorHandled was not raised by the wrapped function")