"""
Unit tests for the logging infrastructure in code/__init__.py
"""

import logging
import sys
from io import StringIO

# Import the logger factory from the package
# We assume the test is run from the project root where 'code' is importable
# or we add the parent directory to sys.path if running in isolation.
try:
    from code import get_logger
except ImportError:
    # Fallback for direct execution in some environments
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from code import get_logger

def test_logger_creation():
    """Test that get_logger returns a valid Logger instance."""
    logger = get_logger("test_logger_creation")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger_creation"

def test_logger_handler_configuration():
    """Test that the logger has a StreamHandler attached."""
    logger = get_logger("test_logger_handler")
    assert len(logger.handlers) > 0
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

def test_logger_output_format(capsys):
    """Test that the logger outputs in the expected format."""
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    logger = get_logger("test_format")
    logger.info("Test message")

    output = sys.stdout.getvalue()
    sys.stdout = old_stdout

    # Check that the message is present
    assert "Test message" in output
    # Check that level is present
    assert "INFO" in output

def test_logger_singleton_behavior():
    """Test that calling get_logger twice for same name returns same handler setup."""
    logger1 = get_logger("test_singleton")
    initial_handler_count = len(logger1.handlers)
    
    logger2 = get_logger("test_singleton")
    
    # Should not add duplicate handlers
    assert len(logger2.handlers) == initial_handler_count
    assert logger1 is logger2