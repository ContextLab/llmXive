import pytest
from code.utils.error_handling import (
    PipelineError,
    DataFetchError,
    DataProcessingError,
    ModelTrainingError,
    ConfigError,
    handle_error,
    validate_not_null,
    validate_positive,
    pipeline_error_handler
)
from code.utils.logger import get_pipeline_logger


logger = get_pipeline_logger()


def test_pipeline_error_hierarchy():
    """Test that specific errors inherit from PipelineError."""
    assert issubclass(DataFetchError, PipelineError)
    assert issubclass(DataProcessingError, PipelineError)
    assert issubclass(ModelTrainingError, PipelineError)
    assert issubclass(ConfigError, PipelineError)


def test_validate_not_null_pass():
    """Test validate_not_null with valid input."""
    assert validate_not_null("value", "test_field") == "value"
    assert validate_not_null(0, "test_field") == 0
    assert validate_not_null(False, "test_field") is False


def test_validate_not_null_fail():
    """Test validate_not_null raises on None."""
    with pytest.raises(DataProcessingError) as exc_info:
        validate_not_null(None, "test_field")
    assert "test_field" in str(exc_info.value)


def test_validate_positive_pass():
    """Test validate_positive with valid input."""
    assert validate_positive(1.0, "test_field") == 1.0
    assert validate_positive(0.001, "test_field") == 0.001
    assert validate_positive(100, "test_field") == 100


def test_validate_positive_fail_zero():
    """Test validate_positive raises on zero."""
    with pytest.raises(DataProcessingError) as exc_info:
        validate_positive(0, "test_field")
    assert "positive" in str(exc_info.value).lower()


def test_validate_positive_fail_negative():
    """Test validate_positive raises on negative."""
    with pytest.raises(DataProcessingError) as exc_info:
        validate_positive(-5, "test_field")
    assert "positive" in str(exc_info.value).lower()


def test_validate_positive_fail_type():
    """Test validate_positive raises on non-numeric."""
    with pytest.raises(DataProcessingError) as exc_info:
        validate_positive("string", "test_field")
    assert "number" in str(exc_info.value).lower()


def test_handle_error_logs_and_reraises():
    """Test that handle_error logs and re-raises by default."""
    with pytest.raises(ValueError) as exc_info:
        try:
            raise ValueError("Test error")
        except ValueError as e:
            handle_error(e, context="Test Context", reraise=True)
    assert "Test error" in str(exc_info.value)


def test_handle_error_logs_no_reraise(capsys):
    """Test that handle_error logs but does not re-raise when requested."""
    try:
        raise ValueError("Test error no reraise")
    except ValueError as e:
        handle_error(e, context="Test Context", reraise=False)
    
    # Verify log output (simplified check)
    captured = capsys.readouterr()
    # The logger writes to file and stdout, checking stdout content
    assert "Test error no reraise" in captured.out or "Test Context" in captured.out


def test_pipeline_error_handler_decorator():
    """Test the decorator handles exceptions correctly."""
    @pipeline_error_handler
    def failing_func():
        raise RuntimeError("Decorated error")

    with pytest.raises(RuntimeError) as exc_info:
        failing_func()
    
    assert "Decorated error" in str(exc_info.value)
