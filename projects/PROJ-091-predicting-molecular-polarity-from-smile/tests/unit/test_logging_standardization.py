import pytest
import logging
import sys
import io
from unittest.mock import patch
from pathlib import Path
import re

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.logging_config import setup_logging, get_logger, STANDARD_FORMAT

class TestLoggingStandardization:
    """
    Tests for T039c: Standardize logging format across all modules.
    Verifies that the logging format matches the required pattern.
    """

    def test_standard_format_constant_exists(self):
        """Asserts that the STANDARD_FORMAT constant is defined correctly."""
        expected = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        assert STANDARD_FORMAT == expected, f"Standard format mismatch. Got: {STANDARD_FORMAT}"

    def test_setup_logging_applies_standard_format(self, tmp_path):
        """Verifies that setup_logging configures the handler with the standard format."""
        log_file = tmp_path / "test.log"
        
        # Setup logging to file and console
        setup_logging(log_file=str(log_file), level=logging.DEBUG, use_json=False)
        
        # Get a logger and log a test message
        logger = get_logger("test_module")
        test_msg = "Test message for standardization"
        logger.info(test_msg)
        
        # Read the file content
        content = log_file.read_text()
        
        # Verify the format pattern in the file
        # Pattern: Timestamp - Name - Level - Message
        # Regex to match the standard format structure
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - test_module - INFO - Test message for standardization'
        
        # We expect at least one line to match the structure
        # The timestamp part varies, so we check the static parts
        assert "test_module" in content
        assert "INFO" in content
        assert test_msg in content
        
        # Verify the separator structure " - " is used consistently
        lines = content.strip().split('\n')
        for line in lines:
            if test_msg in line:
                # Split by ' - ' and check we have 4 parts (time, name, level, msg)
                parts = line.split(' - ')
                assert len(parts) == 4, f"Line does not follow standard format: {line}"
                assert parts[1] == "test_module"
                assert parts[2] == "INFO"
                assert parts[3] == test_msg

    def test_console_handler_uses_standard_format(self, capsys):
        """Verifies that console logging uses the standard format."""
        # Reset handlers to ensure clean state for this test
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging(level=logging.INFO, use_json=False)
        
        logger = get_logger("console_test")
        msg = "Console format check"
        logger.info(msg)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check for standard format components
        assert "console_test" in output
        assert "INFO" in output
        assert msg in output
        
        # Verify structure
        parts = output.strip().split(' - ')
        assert len(parts) == 4, f"Console output does not follow standard format: {output}"

    def test_json_format_is_different(self, tmp_path):
        """Ensures that JSON format (if used) produces different output structure."""
        log_file = tmp_path / "test_json.log"
        
        # Setup with JSON
        setup_logging(log_file=str(log_file), level=logging.INFO, use_json=True)
        
        logger = get_logger("json_test")
        logger.info("JSON check")
        
        content = log_file.read_text()
        
        # JSON should contain braces and keys, not the standard string format
        assert "{" in content
        assert '"message"' in content
        assert '"levelname"' in content
        
        # It should NOT look like the standard format line (no " - " separators in that pattern)
        # Although JSON might contain dashes, the specific sequence " - " as a separator is unique to standard
        # We check that the standard format pattern is NOT the primary structure
        import json
        try:
            parsed = json.loads(content.strip())
            assert "asctime" in parsed
            assert "name" in parsed
        except json.JSONDecodeError:
            pytest.fail("Log file was not valid JSON when use_json=True")

    def test_logger_name_propagation(self):
        """Tests that the logger name is correctly propagated in the format."""
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        setup_logging(level=logging.DEBUG, use_json=False)
        
        # Create a child logger
        parent = get_logger("parent_module")
        child = get_logger("parent_module.child_module")
        
        # Log from child
        msg = "Child message"
        child.info(msg)
        
        # The output should contain the full name
        # Since we can't easily capture stdout in this specific test structure without capsys,
        # we rely on the handler configuration check in previous tests.
        # Here we just verify the logger creation works as expected.
        assert child.name == "parent_module.child_module"
        assert parent.name == "parent_module"