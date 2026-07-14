"""
Test module to verify type hints are correctly defined in utility modules.

This module is used by MyPy to check that all utility functions have proper
type annotations.
"""

from __future__ import annotations

from typing import Any, Dict

from utils.error_handler import PipelineError, handle_error, log_and_exit
from utils.resource_monitor import enforce_limits
from utils.input_validator import (
    validate_file_path,
    validate_file_extension,
    validate_file_mime_type,
    validate_json_schema,
    load_and_validate_yaml,
    validate_json_file,
    validate_csv_file,
    validate_input,
)


def test_error_handler_types() -> None:
    """Test type hints for error_handler module."""
    # Test PipelineError
    error: PipelineError = PipelineError("Test error", 1)
    assert error.message == "Test error"
    assert error.code == 1

    # Test handle_error decorator
    @handle_error
    def sample_func(x: int) -> int:
        return x * 2

    result: int = sample_func(5)
    assert result == 10

    # Test log_and_exit (won't actually exit in tests)
    try:
        log_and_exit(ValueError("Test"), 1)
    except SystemExit:
        pass


def test_resource_monitor_types() -> None:
    """Test type hints for resource_monitor module."""
    # Test enforce_limits
    enforce_limits(max_memory_gb=6.0, max_cpu_cores=2, check_interval=1.0)


def test_input_validator_types() -> None:
    """Test type hints for input_validator module."""
    # Test validate_file_path
    path_result: Any = validate_file_path("/tmp", must_exist=True)

    # Test validate_file_extension
    validate_file_extension("/tmp/test.csv", [".csv"])

    # Test validate_file_mime_type
    validate_file_mime_type("/tmp/test.csv", ["text/csv"])

    # Test validate_json_schema
    test_data: Dict[str, Any] = {"key": "value"}
    test_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {"key": {"type": "string"}},
    }
    validate_json_schema(test_data, test_schema)

    # Test load_and_validate_yaml (would need a real file)
    # validate_and_load_yaml("/tmp/test.yaml", test_schema)

    # Test validate_json_file (would need a real file)
    # validate_json_file("/tmp/test.json", test_schema)

    # Test validate_csv_file (would need a real file)
    # validate_csv_file("/tmp/test.csv", ["col1", "col2"])

    # Test validate_input (would need a real file)
    # validate_input("/tmp/test.json", "json", test_schema)
