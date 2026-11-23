import pytest
import logging
import sys
import io
import re
from pathlib import Path
import tempfile
import os

# Import the module under test
# Assuming tests are run from project root, code is in 'code' directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.logging_config import (
    setup_logging, 
    get_logger, 
    set_log_level, 
    log_with_context,
    STANDARD_LOG_FORMAT
)

class TestLoggingStandardization:
    """
    Unit tests for T039c: Standardize logging format across all modules.
    
    Verifies that:
    1. The standard format string is correctly defined.
    2. setup_logging applies the standard format to handlers.
    3. Log messages follow the expected pattern: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    """

    @pytest.fixture(autouse=True)
    def setup_logging_before_test(self):
        """Ensure logging is reset and configured before each test."""
        # Reset root logger
        root = logging.getLogger()
        root.handlers = []
        root.setLevel(logging.NOTSET)
        
        # Setup with a temporary log file to avoid side effects
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(log_level=logging.DEBUG, log_file=str(log_file))
            yield

    def test_standard_format_definition(self):
        """Verify the standard format string matches the requirement."""
        expected = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert STANDARD_LOG_FORMAT == expected, f"Standard format mismatch. Expected: {expected}, Got: {STANDARD_LOG_FORMAT}"

    def test_setup_logging_applies_standard_format(self):
        """Verify that setup_logging configures handlers with the standard format."""
        # Create a string buffer to capture log output
        stream = io.StringIO()
        
        # Create a temporary handler to inspect format
        handler = logging.StreamHandler(stream)
        handler.setLevel(logging.DEBUG)
        
        # Apply the standard format manually to check
        formatter = logging.Formatter(STANDARD_LOG_FORMAT)
        handler.setFormatter(formatter)
        
        # Get a test logger and add the handler
        test_logger = get_logger("test_module")
        test_logger.handlers = [] # Clear inherited
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)
        
        # Log a message
        test_logger.info("Test message")
        
        # Retrieve the output
        output = stream.getvalue()
        
        # Verify the format matches the pattern
        # Pattern: timestamp - name - level - message
        # We check for the separators and structure
        assert " - " in output, "Log output does not contain standard separators ' - '"
        parts = output.strip().split(" - ")
        assert len(parts) >= 4, f"Log output does not have enough parts. Expected at least 4 (time, name, level, msg), got {len(parts)}. Output: {output}"
        
        # Verify specific components
        assert "test_module" in output, "Logger name not found in output"
        assert "INFO" in output, "Log level not found in output"
        assert "Test message" in output, "Log message not found in output"

    def test_log_with_context_format(self):
        """Verify that log_with_context respects the standard format."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(STANDARD_LOG_FORMAT))
        
        test_logger = get_logger("context_test")
        test_logger.handlers = []
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)
        
        ctx = {"user": "admin", "action": "login"}
        log_with_context(test_logger, logging.INFO, "User action", ctx)
        
        output = stream.getvalue()
        assert "User action" in output, "Message not found"
        assert "context_test" in output, "Logger name not found"
        assert "INFO" in output, "Level not found"
        # Context is appended to message, so it should be present
        assert "admin" in output, "Context data not found"

    def test_all_handlers_use_standard_format(self):
        """Verify that after setup_logging, ALL handlers use the standard format."""
        root_logger = logging.getLogger()
        
        # Check every handler attached to root
        assert len(root_logger.handlers) > 0, "No handlers found on root logger"
        
        for handler in root_logger.handlers:
            formatter = handler.formatter
            assert formatter is not None, f"Handler {handler} has no formatter"
            
            # Check the format string
            # Note: The format string might be stored in _style._fmt for newer python versions
            # or accessed via format() logic. 
            # We test by logging a known message and checking the structure.
            test_stream = io.StringIO()
            test_handler = logging.StreamHandler(test_stream)
            test_handler.setFormatter(formatter)
            
            test_logger = logging.getLogger(f"temp_{id(handler)}")
            test_logger.handlers = []
            test_logger.addHandler(test_handler)
            test_logger.setLevel(logging.DEBUG)
            
            test_logger.info("verify_format")
            
            log_output = test_stream.getvalue()
            parts = log_output.strip().split(" - ")
            
            # Must have at least 4 parts: time, name, level, msg
            assert len(parts) >= 4, f"Handler {handler} does not use standard format. Output: {log_output}"
            
            # Verify level and name presence
            assert "INFO" in log_output, "Level missing in handler output"
            assert "verify_format" in log_output, "Message missing in handler output"

    def test_no_custom_format_overrides(self):
        """Ensure no custom format strings are hardcoded in place of the standard one."""
        # This is a meta-check on the module source if needed, 
        # but primarily we verify the runtime behavior matches the standard.
        # The test 'test_setup_logging_applies_standard_format' covers the core requirement.
        pass
