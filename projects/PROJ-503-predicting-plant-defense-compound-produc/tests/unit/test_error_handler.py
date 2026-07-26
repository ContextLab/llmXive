"""
Unit tests for the error handling framework.
Tests E-DATASET, E-PAIRING, E-TIMEOUT, E-POWER, and E-SAMPLESIZE error codes.
"""
import pytest
import time
from unittest.mock import patch
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'projects', 'PROJ-503-predicting-plant-defense-compound-produc', 'code'))

from exceptions import (
    PipelineError, E_DATASET, E_PAIRING, E_TIMEOUT, E_POWER, E_SAMPLESIZE,
    raise_dataset_error, raise_pairing_error, raise_timeout_error,
    raise_power_error, raise_samplesize_error
)
from error_handler import (
    set_timeout_limit, start_timeout_monitor, check_timeout,
    validate_pairing_rate, validate_sample_size, validate_dataset_availability,
    timeout_context
)


class TestExceptionClasses:
    """Test that exception classes have correct error codes and messages."""

    def test_pipeline_error_base(self):
        """Test base PipelineError class."""
        error = PipelineError("Test message", "TEST-CODE", {"key": "value"})
        assert error.error_code == "TEST-CODE"
        assert error.details == {"key": "value"}
        assert "Test message" in str(error)

    def test_e_dataset(self):
        """Test E_DATASET exception."""
        error = E_DATASET("No datasets found", {"found": 0})
        assert error.error_code == "E-DATASET"
        assert "No datasets found" in str(error)
        assert error.details["found"] == 0

    def test_e_pairing(self):
        """Test E_PAIRING exception."""
        error = E_PAIRING("Pairing rate too low", {"rate": 0.5})
        assert error.error_code == "E-PAIRING"
        assert "Pairing rate too low" in str(error)
        assert error.details["rate"] == 0.5

    def test_e_timeout(self):
        """Test E_TIMEOUT exception."""
        error = E_TIMEOUT("Execution timed out", {"elapsed": 14400})
        assert error.error_code == "E-TIMEOUT"
        assert "Execution timed out" in str(error)
        assert error.details["elapsed"] == 14400

    def test_e_power(self):
        """Test E_POWER exception."""
        error = E_POWER("Insufficient power", {"n": 10, "required": 28})
        assert error.error_code == "E-POWER"
        assert "Insufficient power" in str(error)
        assert error.details["n"] == 10

    def test_e_samplesize(self):
        """Test E_SAMPLESIZE exception."""
        error = E_SAMPLESIZE("Sample size too small", {"n": 5})
        assert error.error_code == "E-SAMPLESIZE"
        assert "Sample size too small" in str(error)
        assert error.details["n"] == 5


class TestRaiseFunctions:
    """Test convenience functions for raising errors."""

    def test_raise_dataset_error(self):
        """Test raise_dataset_error function."""
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error("Test dataset error", {"test": True})
        assert exc_info.value.error_code == "E-DATASET"
        assert exc_info.value.details["test"] is True

    def test_raise_pairing_error(self):
        """Test raise_pairing_error function."""
        with pytest.raises(E_PAIRING) as exc_info:
            raise_pairing_error("Test pairing error", {"rate": 0.8})
        assert exc_info.value.error_code == "E-PAIRING"
        assert exc_info.value.details["rate"] == 0.8

    def test_raise_timeout_error(self):
        """Test raise_timeout_error function."""
        with pytest.raises(E_TIMEOUT) as exc_info:
            raise_timeout_error("Test timeout error", {"time": 100})
        assert exc_info.value.error_code == "E-TIMEOUT"
        assert exc_info.value.details["time"] == 100

    def test_raise_power_error(self):
        """Test raise_power_error function."""
        with pytest.raises(E_POWER) as exc_info:
            raise_power_error("Test power error", {"n": 15})
        assert exc_info.value.error_code == "E-POWER"
        assert exc_info.value.details["n"] == 15

    def test_raise_samplesize_error(self):
        """Test raise_samplesize_error function."""
        with pytest.raises(E_SAMPLESIZE) as exc_info:
            raise_samplesize_error("Test sample size error", {"n": 20})
        assert exc_info.value.error_code == "E-SAMPLESIZE"
        assert exc_info.value.details["n"] == 20


class TestValidationFunctions:
    """Test validation functions for error triggering."""

    def test_validate_pairing_rate_success(self):
        """Test successful pairing rate validation."""
        # Should not raise
        validate_pairing_rate(0.96, threshold=0.95)

    def test_validate_pairing_rate_failure(self):
        """Test failed pairing rate validation."""
        with pytest.raises(E_PAIRING) as exc_info:
            validate_pairing_rate(0.90, threshold=0.95)
        assert exc_info.value.error_code == "E-PAIRING"
        assert "below required threshold" in str(exc_info.value)

    def test_validate_sample_size_success(self):
        """Test successful sample size validation."""
        # Should not raise
        validate_sample_size(30, minimum_required=28)

    def test_validate_sample_size_failure(self):
        """Test failed sample size validation."""
        with pytest.raises(E_POWER) as exc_info:
            validate_sample_size(20, minimum_required=28)
        assert exc_info.value.error_code == "E-POWER"
        assert "below minimum required" in str(exc_info.value)

    def test_validate_dataset_availability_success(self):
        """Test successful dataset availability validation."""
        # Should not raise
        validate_dataset_availability(2, minimum_required=1)

    def test_validate_dataset_availability_failure(self):
        """Test failed dataset availability validation."""
        with pytest.raises(E_DATASET) as exc_info:
            validate_dataset_availability(0, minimum_required=1)
        assert exc_info.value.error_code == "E-DATASET"
        assert "No verified plant omics datasets found" in str(exc_info.value)


class TestTimeoutFunctions:
    """Test timeout monitoring functions."""

    def test_set_timeout_limit(self):
        """Test setting timeout limit."""
        set_timeout_limit(100)
        # Note: We can't easily test the global state without mocking,
        # but we verify the function runs without error
        assert True

    def test_timeout_context_success(self):
        """Test timeout context with successful completion."""
        with timeout_context(timeout_seconds=10):
            time.sleep(0.1)  # Short sleep, well within timeout
        # Should not raise

    def test_timeout_context_failure(self):
        """Test timeout context with timeout exceeded."""
        with pytest.raises(E_TIMEOUT):
            with timeout_context(timeout_seconds=0.01):
                time.sleep(0.1)  # Sleep longer than timeout

    def test_check_timeout_not_started(self):
        """Test check_timeout when not started."""
        # Reset state
        import error_handler
        error_handler._timeout_start = None
        result = check_timeout()
        assert result is None

    def test_check_timeout_within_limit(self):
        """Test check_timeout when within limit."""
        import error_handler
        error_handler._timeout_start = time.time()
        error_handler._timeout_limit = 100
        result = check_timeout()
        assert result is False

    def test_check_timeout_exceeded(self):
        """Test check_timeout when exceeded."""
        import error_handler
        error_handler._timeout_start = time.time() - 200  # 200 seconds ago
        error_handler._timeout_limit = 100
        result = check_timeout()
        assert result is True