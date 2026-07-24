"""
Unit tests for the error handling framework.

Tests E-DATASET, E-PAIRING, E-TIMEOUT, and E-POWER error codes
and the error handling utilities.
"""
import pytest
import time
import sys
from unittest.mock import patch, MagicMock

# Import from the project
sys.path.insert(0, 'projects/PROJ-503-predicting-plant-defense-compound-produc/code')

from exceptions import (
    PipelineError,
    E_DATASET,
    E_PAIRING,
    E_TIMEOUT,
    E_POWER,
    ERROR_CODES,
    ERROR_DESCRIPTIONS
)
from error_handler import (
    set_timeout_limit,
    start_timeout_monitor,
    check_timeout,
    handle_error,
    raise_dataset_error,
    raise_pairing_error,
    raise_timeout_error,
    raise_power_error,
    validate_pairing_rate,
    validate_sample_size,
    wrap_with_timeout
)


class TestExceptionClasses:
    """Tests for custom exception classes."""
    
    def test_pipeline_error_base(self):
        """Test base PipelineError class."""
        error = PipelineError("Test message", "TEST-CODE", {"key": "value"})
        assert error.message == "Test message"
        assert error.code == "TEST-CODE"
        assert error.details == {"key": "value"}
        assert "TEST-CODE" in str(error)
        assert "value" in str(error)
    
    def test_e_dataset(self):
        """Test E_DATASET exception."""
        error = E_DATASET("No data found", {"source": "GEO"})
        assert error.code == "E-DATASET"
        assert error.message == "No data found"
        assert error.details == {"source": "GEO"}
    
    def test_e_pairing(self):
        """Test E_PAIRING exception."""
        error = E_PAIRING("Low pairing rate", {"rate": 0.8})
        assert error.code == "E-PAIRING"
        assert error.message == "Low pairing rate"
        assert error.details == {"rate": 0.8}
    
    def test_e_timeout(self):
        """Test E_TIMEOUT exception."""
        error = E_TIMEOUT("Time limit exceeded", {"elapsed": 14401})
        assert error.code == "E-TIMEOUT"
        assert error.message == "Time limit exceeded"
        assert error.details == {"elapsed": 14401}
    
    def test_e_power(self):
        """Test E_POWER exception."""
        error = E_POWER("Insufficient samples", {"n": 20})
        assert error.code == "E-POWER"
        assert error.message == "Insufficient samples"
        assert error.details == {"n": 20}
    
    def test_error_codes_mapping(self):
        """Test ERROR_CODES dictionary."""
        assert ERROR_CODES["E-DATASET"] == E_DATASET
        assert ERROR_CODES["E-PAIRING"] == E_PAIRING
        assert ERROR_CODES["E-TIMEOUT"] == E_TIMEOUT
        assert ERROR_CODES["E-POWER"] == E_POWER
    
    def test_error_descriptions(self):
        """Test ERROR_DESCRIPTIONS dictionary."""
        assert "Data availability" in ERROR_DESCRIPTIONS["E-DATASET"]
        assert "Pairing" in ERROR_DESCRIPTIONS["E-PAIRING"]
        assert "Timeout" in ERROR_DESCRIPTIONS["E-TIMEOUT"]
        assert "Power" in ERROR_DESCRIPTIONS["E-POWER"]


class TestTimeoutHandling:
    """Tests for timeout management."""
    
    def test_set_timeout_limit(self):
        """Test setting timeout limit."""
        set_timeout_limit(100)
        # Note: We can't easily check the global variable here without importing
        # the module state, but we verify the function doesn't crash
    
    def test_start_timeout_monitor(self):
        """Test starting timeout monitor."""
        start_timeout_monitor()
        # Verify it sets the start time without crashing
    
    def test_check_timeout_no_start(self):
        """Test check_timeout when monitor not started."""
        # Should not raise if monitor not started
        check_timeout()
    
    def test_check_timeout_not_exceeded(self):
        """Test check_timeout when time not exceeded."""
        start_timeout_monitor()
        # Should not raise immediately
        check_timeout()
    
    def test_check_timeout_exceeded(self):
        """Test check_timeout when time is exceeded."""
        # Mock time to simulate timeout
        with patch('error_handler.time.time', return_value=1000):
            with patch('error_handler._timeout_start_time', 0):
                with patch('error_handler._timeout_limit', 10):
                    with pytest.raises(E_TIMEOUT):
                        check_timeout()
    
    def test_validate_sample_size_pass(self):
        """Test sample size validation with sufficient samples."""
        # Should not raise
        validate_sample_size(30, min_required=28)
    
    def test_validate_sample_size_fail(self):
        """Test sample size validation with insufficient samples."""
        with pytest.raises(E_POWER):
            validate_sample_size(20, min_required=28)
    
    def test_validate_pairing_rate_pass(self):
        """Test pairing rate validation with sufficient rate."""
        # Should not raise
        validate_pairing_rate(0.96, threshold=0.95)
    
    def test_validate_pairing_rate_fail(self):
        """Test pairing rate validation with insufficient rate."""
        with pytest.raises(E_PAIRING):
            validate_pairing_rate(0.90, threshold=0.95)
    
    def test_validate_pairing_rate_with_details(self):
        """Test that E_PAIRING includes details on failure."""
        with pytest.raises(E_PAIRING) as exc_info:
            validate_pairing_rate(0.80, threshold=0.95)
        assert exc_info.value.details["pairing_rate"] == 0.80
        assert exc_info.value.details["threshold"] == 0.95


class TestErrorRaising:
    """Tests for error raising functions."""
    
    def test_raise_dataset_error(self):
        """Test raising E_DATASET."""
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error("Test error", {"key": "val"})
        assert exc_info.value.code == "E-DATASET"
        assert exc_info.value.details == {"key": "val"}
    
    def test_raise_pairing_error(self):
        """Test raising E_PAIRING."""
        with pytest.raises(E_PAIRING) as exc_info:
            raise_pairing_error("Test error")
        assert exc_info.value.code == "E-PAIRING"
    
    def test_raise_timeout_error(self):
        """Test raising E_TIMEOUT."""
        with pytest.raises(E_TIMEOUT) as exc_info:
            raise_timeout_error("Test error")
        assert exc_info.value.code == "E-TIMEOUT"
    
    def test_raise_power_error(self):
        """Test raising E_POWER."""
        with pytest.raises(E_POWER) as exc_info:
            raise_power_error("Test error")
        assert exc_info.value.code == "E-POWER"

class TestErrorHandler:
    """Tests for handle_error function."""
    
    def test_handle_error_logging(self, caplog):
        """Test that handle_error logs the error."""
        error = E_DATASET("Test error")
        with caplog.at_level("CRITICAL"):
            handle_error(error, exit_on_error=False)
        assert "E-DATASET" in caplog.text
        assert "Test error" in caplog.text
    
    def test_handle_error_exit(self):
        """Test that handle_error exits when configured."""
        error = E_PAIRING("Test error")
        with patch('sys.exit') as mock_exit:
            handle_error(error, exit_on_error=True)
            mock_exit.assert_called_once_with(1)

class TestTimeoutDecorator:
    """Tests for wrap_with_timeout decorator."""
    
    def test_decorator_success(self):
        """Test decorator when function completes in time."""
        @wrap_with_timeout(timeout_seconds=10)
        def quick_function():
            return "success"
        
        result = quick_function()
        assert result == "success"
    
    def test_decorator_timeout(self):
        """Test decorator when function exceeds timeout."""
        @wrap_with_timeout(timeout_seconds=0.1)
        def slow_function():
            time.sleep(1)
            return "should not reach"
        
        with pytest.raises(E_TIMEOUT):
            slow_function()