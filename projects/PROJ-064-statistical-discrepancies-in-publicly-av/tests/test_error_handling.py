"""
Unit tests for error handling utilities.
"""
import pytest
from unittest.mock import patch, MagicMock
import logging
from functools import wraps

from exceptions import (
    DiscrepancyError,
    DataAcquisitionError,
    MissingDataError,
    ValidationFailureError,
    StatisticalModelError,
    ConfigurationError
)
from error_handling import (
    handle_errors,
    validate_required_fields,
    safe_execute,
    error_handler_factory,
    log_function_call,
    validate_input_types
)
from logger import setup_logging, get_logger

@pytest.fixture(autouse=True)
def setup_logging_fixture():
    """Setup logging for tests."""
    setup_logging(log_level="DEBUG", console=True)

class TestHandleErrors:
    """Tests for handle_errors decorator."""
    
    def test_success_case(self):
        """Test decorator with successful function execution."""
        @handle_errors(reraise=False)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_discrepancy_error_handling(self):
        """Test handling of DiscrepancyError."""
        @handle_errors(reraise=False, fallback="fallback_value")
        def failing_func():
            raise DiscrepancyError("Test error", code="TEST_001")
        
        result = failing_func()
        assert result == "fallback_value"
    
    def test_reraise_true(self):
        """Test that exception is re-raised when reraise=True."""
        @handle_errors(reraise=True)
        def failing_func():
            raise DiscrepancyError("Test error")
        
        with pytest.raises(DiscrepancyError):
            failing_func()
    
    def test_unexpected_exception_handling(self):
        """Test handling of unexpected exceptions."""
        @handle_errors(reraise=False, fallback="fallback")
        def failing_func():
            raise ValueError("Unexpected error")
        
        result = failing_func()
        assert result == "fallback"
    
    def test_with_context(self):
        """Test decorator with additional context."""
        @handle_errors(context={"test_id": 123})
        def failing_func():
            raise DiscrepancyError("Test error")
        
        # Should raise, but context should be logged
        with pytest.raises(DiscrepancyError):
            failing_func()

class TestValidateRequiredFields:
    """Tests for validate_required_fields function."""
    
    def test_all_fields_present(self):
        """Test validation when all fields are present."""
        data = {"field1": "value1", "field2": "value2", "field3": "value3"}
        
        # Should not raise
        validate_required_fields(data, ["field1", "field2", "field3"])
    
    def test_missing_field(self):
        """Test validation when a field is missing."""
        data = {"field1": "value1", "field2": "value2"}
        
        with pytest.raises(MissingDataError) as exc_info:
            validate_required_fields(data, ["field1", "field2", "field3"])
        
        assert "field3" in str(exc_info.value)
    
    def test_multiple_missing_fields(self):
        """Test validation when multiple fields are missing."""
        data = {"field1": "value1"}
        
        with pytest.raises(MissingDataError) as exc_info:
            validate_required_fields(data, ["field2", "field3", "field4"])
        
        assert "field2" in str(exc_info.value)
        assert "field3" in str(exc_info.value)
        assert "field4" in str(exc_info.value)
    
    def test_none_value_treated_as_missing(self):
        """Test that None values are treated as missing."""
        data = {"field1": "value1", "field2": None}
        
        with pytest.raises(MissingDataError):
            validate_required_fields(data, ["field1", "field2"])
    
    def test_custom_error_class(self):
        """Test with custom error class."""
        data = {"field1": "value1"}
        
        with pytest.raises(ConfigurationError):
            validate_required_fields(
                data,
                ["field2"],
                error_class=ConfigurationError
            )
    
    def test_custom_error_message_template(self):
        """Test with custom error message template."""
        data = {"field1": "value1"}
        
        with pytest.raises(MissingDataError) as exc_info:
            validate_required_fields(
                data,
                ["field2"],
                error_message_template="Custom: {missing_fields}"
            )
        
        assert "Custom:" in str(exc_info.value)

class TestSafeExecute:
    """Tests for safe_execute function."""
    
    def test_success_case(self):
        """Test safe_execute with successful function."""
        def success_func():
            return "success"
        
        result = safe_execute(success_func)
        assert result == "success"
    
    def test_failure_with_fallback(self):
        """Test safe_execute with fallback value."""
        def failing_func():
            raise ValueError("Error")
        
        result = safe_execute(failing_func, fallback="fallback")
        assert result == "fallback"
    
    def test_failure_without_fallback(self):
        """Test safe_execute without fallback (returns None)."""
        def failing_func():
            raise ValueError("Error")
        
        result = safe_execute(failing_func)
        assert result is None
    
    def test_with_args_and_kwargs(self):
        """Test safe_execute with arguments."""
        def add_func(a, b, c=0):
            return a + b + c
        
        result = safe_execute(add_func, 1, 2, c=3)
        assert result == 6
    
    def test_log_errors_disabled(self):
        """Test safe_execute with logging disabled."""
        def failing_func():
            raise ValueError("Error")
        
        # Should not log
        result = safe_execute(failing_func, fallback="fallback", log_errors=False)
        assert result == "fallback"

class TestErrorHandlerFactory:
    """Tests for error_handler_factory function."""
    
    def test_factory_creates_decorator(self):
        """Test that factory returns a decorator."""
        handler = error_handler_factory()
        
        @handler
        def test_func():
            return "success"
        
        assert callable(test_func)
    
    def test_wraps_exception(self):
        """Test that non-DiscrepancyError is wrapped."""
        handler = error_handler_factory(
            default_error_class=ConfigurationError,
            default_code="TEST_001"
        )
        
        @handler
        def failing_func():
            raise ValueError("Original error")
        
        with pytest.raises(ConfigurationError) as exc_info:
            failing_func()
        
        assert "TEST_001" in str(exc_info.value)
        assert "Original error" in str(exc_info.value)
    
    def test_discrepancy_error_passthrough(self):
        """Test that DiscrepancyError is not wrapped."""
        handler = error_handler_factory()
        
        @handler
        def failing_func():
            raise DiscrepancyError("Original error", code="ORIGINAL_001")
        
        with pytest.raises(DiscrepancyError) as exc_info:
            failing_func()
        
        assert exc_info.value.code == "ORIGINAL_001"

class TestLogFunctionCall:
    """Tests for log_function_call decorator."""
    
    def test_logs_entry_and_exit(self):
        """Test that function entry and exit are logged."""
        @log_function_call
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_logs_error_on_exception(self):
        """Test that errors are logged on exception."""
        @log_function_call
        def failing_func():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            failing_func()
    
    def test_preserves_function_metadata(self):
        """Test that function metadata is preserved."""
        @log_function_call
        def test_func():
            """Docstring."""
            return "success"
        
        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Docstring."

class TestValidateInputTypes:
    """Tests for validate_input_types decorator factory."""
    
    def test_valid_types(self):
        """Test when all types are valid."""
        validator = validate_input_types({"x": int, "y": str})
        
        @validator
        def test_func(x: int, y: str):
            return x, y
        
        result = test_func(1, "test")
        assert result == (1, "test")
    
    def test_invalid_type(self):
        """Test when a type is invalid."""
        validator = validate_input_types({"x": int, "y": str})
        
        @validator
        def test_func(x: int, y: str):
            return x, y
        
        with pytest.raises(ConfigurationError):
            test_func("not_int", "test")
    
    def test_custom_error_class(self):
        """Test with custom error class."""
        validator = validate_input_types(
            {"x": int},
            error_class=DiscrepancyError
        )
        
        @validator
        def test_func(x: int):
            return x
        
        with pytest.raises(DiscrepancyError):
            test_func("not_int")
    
    def test_optional_parameters(self):
        """Test with optional parameters."""
        validator = validate_input_types({"x": int})
        
        @validator
        def test_func(x: int, y: str = "default"):
            return x, y
        
        result = test_func(1)
        assert result == (1, "default")