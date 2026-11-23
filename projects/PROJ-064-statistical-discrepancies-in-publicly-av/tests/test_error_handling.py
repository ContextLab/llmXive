"""
Unit tests for the error handling framework.
"""
import pytest
from unittest.mock import Mock, patch
import logging

from exceptions import (
    DiscrepancyError,
    DataAcquisitionError,
    MissingDataError,
    ValidationFailureError,
    StatisticalModelError,
    ConfigurationError,
    ReproducibilityError
)

from error_handling import (
    error_handler_factory,
    handle_errors,
    safe_execute,
    validate_required_fields,
    validate_input_types,
    log_function_call
)


class TestExceptions:
    """Tests for custom exception classes."""
    
    def test_discrepancy_error_basic(self):
        """Test basic DiscrepancyError creation."""
        error = DiscrepancyError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {}
    
    def test_discrepancy_error_with_context(self):
        """Test DiscrepancyError with context."""
        error = DiscrepancyError("Test error", context={"key": "value"})
        assert error.context == {"key": "value"}
    
    def test_subclass_errors(self):
        """Test that all subclasses inherit from DiscrepancyError."""
        errors = [
            DataAcquisitionError("msg"),
            MissingDataError("msg"),
            ValidationFailureError("msg"),
            StatisticalModelError("msg"),
            ConfigurationError("msg"),
            ReproducibilityError("msg")
        ]
        
        for error in errors:
            assert isinstance(error, DiscrepancyError)


class TestErrorHandlerFactory:
    """Tests for the error_handler_factory decorator."""
    
    def test_handles_discrepancy_error(self):
        """Test handling of DiscrepancyError."""
        @error_handler_factory(re_raise=False)
        def failing_func():
            raise DiscrepancyError("Test error")
        
        result = failing_func()
        assert result is None
    
    def test_re_raises_by_default(self):
        """Test that exceptions are re-raised by default."""
        @error_handler_factory()
        def failing_func():
            raise DiscrepancyError("Test error")
        
        with pytest.raises(DiscrepancyError):
            failing_func()
    
    def test_handles_unexpected_errors(self):
        """Test handling of unexpected exceptions."""
        @error_handler_factory(default_error=ConfigurationError, re_raise=False)
        def failing_func():
            raise ValueError("Unexpected error")
        
        result = failing_func()
        assert result is None


class TestHandleErrors:
    """Tests for the handle_errors decorator."""
    
    def test_wraps_function_successfully(self):
        """Test that successful functions are wrapped correctly."""
        @handle_errors(error_type=DiscrepancyError)
        def success_func():
            return "success"
        
        assert success_func() == "success"
    
    def test_raises_custom_error_on_failure(self):
        """Test that a custom error is raised on failure."""
        @handle_errors(error_type=MissingDataError, message="Custom message")
        def failing_func():
            raise ValueError("Original error")
        
        with pytest.raises(MissingDataError, match="Custom message"):
            failing_func()


class TestSafeExecute:
    """Tests for the safe_execute decorator."""
    
    def test_returns_default_on_exception(self):
        """Test that default value is returned on exception."""
        @safe_execute(default_value="default")
        def failing_func():
            raise ValueError("Error")
        
        assert failing_func() == "default"
    
    def test_returns_result_on_success(self):
        """Test that result is returned on success."""
        @safe_execute(default_value="default")
        def success_func():
            return "success"
        
        assert success_func() == "success"
    
    def test_catches_specific_exceptions(self):
        """Test that only specific exceptions are caught."""
        @safe_execute(default_value="default", catch_exceptions=[ValueError])
        def failing_func():
            raise TypeError("Wrong type")
        
        with pytest.raises(TypeError):
            failing_func()


class TestValidateRequiredFields:
    """Tests for validate_required_fields function."""
    
    def test_passes_when_all_fields_present(self):
        """Test validation passes when all fields are present."""
        data = {"field1": 1, "field2": 2}
        validate_required_fields(data, ["field1", "field2"])
    
    def test_raises_when_fields_missing(self):
        """Test that ValidationFailureError is raised when fields are missing."""
        data = {"field1": 1}
        
        with pytest.raises(ValidationFailureError) as exc_info:
            validate_required_fields(data, ["field1", "field2"])
        
        assert "field2" in str(exc_info.value)
    
    def test_includes_context_in_error(self):
        """Test that error includes context about missing fields."""
        data = {"field1": 1}
        
        with pytest.raises(ValidationFailureError) as exc_info:
            validate_required_fields(data, ["field2"])
        
        assert exc_info.value.context["missing_fields"] == ["field2"]


class TestValidateInputTypes:
    """Tests for validate_input_types function."""
    
    def test_passes_when_type_matches(self):
        """Test validation passes when type matches."""
        validate_input_types(123, int)
    
    def test_raises_when_type_mismatch(self):
        """Test that ValidationFailureError is raised on type mismatch."""
        with pytest.raises(ValidationFailureError) as exc_info:
            validate_input_types("string", int)
        
        assert "int" in str(exc_info.value)
    
    def test_includes_field_name_in_error(self):
        """Test that field name is included in error message."""
        with pytest.raises(ValidationFailureError) as exc_info:
            validate_input_types("string", int, field_name="my_field")
        
        assert "my_field" in str(exc_info.value)


class TestLogFunctionCall:
    """Tests for the log_function_call decorator."""
    
    def test_logs_entry_and_exit(self):
        """Test that function entry and exit are logged."""
        logger = logging.getLogger("test_log_call")
        logger.handlers.clear()
        
        stream = logging.StreamHandler()
        stream.setLevel(logging.DEBUG)
        logger.addHandler(stream)
        logger.setLevel(logging.DEBUG)
        
        @log_function_call
        def test_func(x, y=10):
            return x + y
        
        result = test_func(5, y=20)
        assert result == 25