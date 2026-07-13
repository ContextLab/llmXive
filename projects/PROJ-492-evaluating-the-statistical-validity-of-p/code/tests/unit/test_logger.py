"""
Unit tests for the structured logging infrastructure (T009).

Verifies that:
1. The logger is properly configured.
2. Error codes in the format ERR-### are correctly formatted and logged.
3. The error code registry contains all expected codes.
4. JSON formatting includes error codes when present.
"""

import json
import logging
import sys
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.utils.logger import (
    AuditLogger,
    JsonFormatter,
    get_default_logger,
    get_error_message,
    ERROR_CODES,
)


def test_error_code_format():
    """Verify error codes follow ERR-### format."""
    for code in ERROR_CODES.keys():
        assert code.startswith("ERR-"), f"Error code {code} does not start with 'ERR-'"
        assert len(code) == 7, f"Error code {code} is not 7 characters long"
        assert code[4:7].isdigit(), f"Error code {code} does not end with 3 digits"
    print("✓ All error codes follow ERR-### format")


def test_get_error_message():
    """Verify error message retrieval works correctly."""
    assert get_error_message("ERR-001") == "Missing required metric in A/B test summary"
    assert get_error_message("ERR-201") == "Export validation: audit_report.json and summary_report.csv counts do not match"
    assert "Unknown error code" in get_error_message("ERR-999")
    print("✓ Error message retrieval works correctly")


def test_json_formatter_includes_error_code():
    """Verify JSON formatter includes error code in output."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="test.py",
        lineno=1,
        msg="Test error message",
        args=(),
        exc_info=None,
    )
    record.error_code = "ERR-001"
    record.error_description = "Missing required metric"

    output = formatter.format(record)
    log_data = json.loads(output)

    assert log_data["error_code"] == "ERR-001"
    assert log_data["error_description"] == "Missing required metric"
    assert "Test error message" in log_data["message"]
    print("✓ JSON formatter includes error code in output")


def test_audit_logger_log_with_code():
    """Verify AuditLogger.log_with_code formats messages correctly."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    base_logger = logging.getLogger("test_audit_logger")
    base_logger.handlers = [handler]
    base_logger.setLevel(logging.DEBUG)

    audit_logger = AuditLogger(base_logger)

    # Log with error code
    audit_logger.log_with_code(logging.ERROR, "Test message", error_code="ERR-050")

    output = stream.getvalue()
    log_data = json.loads(output)

    assert log_data["error_code"] == "ERR-050"
    assert "Test message" in log_data["message"]
    print("✓ AuditLogger.log_with_code formats messages correctly")


def test_get_default_logger_configuration():
    """Verify get_default_logger returns a properly configured logger."""
    logger = get_default_logger("test_default")

    assert isinstance(logger, AuditLogger)
    assert len(logger.logger.handlers) >= 1
    assert logger.logger.level == logging.DEBUG
    print("✓ get_default_logger returns a properly configured logger")


def test_logger_error_method_with_code():
    """Verify logger.error() accepts and formats error_code parameter."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())

    base_logger = logging.getLogger("test_error_method")
    base_logger.handlers = [handler]
    base_logger.setLevel(logging.DEBUG)

    audit_logger = AuditLogger(base_logger)

    audit_logger.error("Error occurred", error_code="ERR-301")

    output = stream.getvalue()
    log_data = json.loads(output)

    assert log_data["error_code"] == "ERR-301"
    assert "Resource limit exceeded" in log_data["error_description"]
    print("✓ logger.error() accepts and formats error_code parameter")


def test_all_defined_errors_have_descriptions():
    """Verify all error codes have non-empty descriptions."""
    for code, desc in ERROR_CODES.items():
        assert desc, f"Error code {code} has an empty description"
        assert len(desc) > 10, f"Error code {code} has a description that is too short: '{desc}'"
    print("✓ All defined error codes have meaningful descriptions")


if __name__ == "__main__":
    test_error_code_format()
    test_get_error_message()
    test_json_formatter_includes_error_code()
    test_audit_logger_log_with_code()
    test_get_default_logger_configuration()
    test_logger_error_method_with_code()
    test_all_defined_errors_have_descriptions()
    print("\n✅ All T009 logger tests passed successfully.")
