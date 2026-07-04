import logging
import sys
from io import StringIO

import pytest

# Import the function to test
from src.logging_config import setup_logging, get_logger


def test_setup_logging_format():
    """
    Verify that the root logger is configured with the correct format:
    '%(asctime)s - %(levelname)s - %(message)s'
    """
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        logger = setup_logging(log_level="INFO")

        # Verify the root logger has handlers
        assert len(logger.handlers) == 1

        handler = logger.handlers[0]
        formatter = handler.formatter

        # Check the format string
        assert formatter._fmt == "%(asctime)s - %(levelname)s - %(message)s"

        # Check the level
        assert logger.level == logging.INFO
    finally:
        sys.stdout = old_stdout


def test_setup_logging_output():
    """
    Verify that logging a message produces output in the expected format.
    """
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        logger = setup_logging(log_level="INFO")

        # Log a test message
        logger.info("Test message")

        output = sys.stdout.getvalue()

        # The output should contain the message and the level
        assert "Test message" in output
        assert "INFO" in output
        # The format is 'timestamp - LEVEL - message', so we expect the hyphen separators
        assert " - " in output
    finally:
        sys.stdout = old_stdout


def test_get_logger_returns_configured_logger():
    """
    Verify that get_logger returns a logger that inherits the root configuration.
    """
    setup_logging(log_level="DEBUG")

    child_logger = get_logger("test_module")

    assert child_logger.level == logging.NOTSET  # Child loggers usually inherit
    assert child_logger.parent is not None
    assert child_logger.parent.name == "root"

    # Verify it can log
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        child_logger.debug("Child debug message")
        output = sys.stdout.getvalue()
        # Since root is DEBUG, this should appear
        assert "Child debug message" in output
    finally:
        sys.stdout = old_stdout


def test_setup_logging_clears_existing_handlers():
    """
    Verify that setup_logging clears any existing handlers to prevent duplicates.
    """
    # Pre-populate root with a dummy handler
    root_logger = logging.getLogger()
    dummy_handler = logging.NullHandler()
    root_logger.addHandler(dummy_handler)

    try:
        setup_logging(log_level="WARNING")

        # The dummy handler should be gone, replaced by the new console handler
        assert dummy_handler not in root_logger.handlers
        assert len(root_logger.handlers) == 1
    finally:
        # Clean up
        root_logger.handlers.clear()
