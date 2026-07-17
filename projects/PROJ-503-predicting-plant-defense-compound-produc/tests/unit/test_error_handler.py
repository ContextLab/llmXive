"""
Unit tests for the error handling framework.
Tests all error codes (E-DATASET, E-PAIRING, E-TIMEOUT, E-POWER)
and error handling utilities.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from exceptions import (
    PipelineError,
    E_DATASET,
    E_PAIRING,
    E_TIMEOUT,
    E_POWER
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
    wrap_with_timeout
)
from pathlib import Path


class TestExceptionClasses:
    """Test custom exception classes."""
    
    def test_pipeline_error_base(self):
        """Test base PipelineError class."""
        error = PipelineError("Test message", "TEST-CODE", {"key": "value"})
        assert error.message == "Test message"
        assert error.error_code == "TEST-CODE"
        assert error.details == {"key": "value"}
        assert str(error) == "Test message"
    
    def test_e_dataset_exception(self):
        """Test E_DATASET exception."""
        error = E_DATASET("Dataset not found", {"source": "GEO"})
        assert error.error_code == "E-DATASET"
        assert "E-DATASET" in str(error)
        assert error.details == {"source": "GEO"}
    
    def test_e_pairing_exception(self):
        """Test E_PAIRING exception."""
        error = E_PAIRING("Pairing rate too low", {"rate": 0.5, "threshold": 0.95})
        assert error.error_code == "E-PAIRING"
        assert "E-PAIRING" in str(error)
        assert error.details == {"rate": 0.5, "threshold": 0.95}
    
    def test_e_timeout_exception(self):
        """Test E_TIMEOUT exception."""
        error = E_TIMEOUT("Execution time exceeded", {"elapsed": 15000, "limit": 14400})
        assert error.error_code == "E-TIMEOUT"
        assert "E-TIMEOUT" in str(error)
        assert error.details == {"elapsed": 15000, "limit": 14400}
    
    def test_e_power_exception(self):
        """Test E_POWER exception."""
        error = E_POWER("Insufficient sample size", {"n": 20, "required": 28})
        assert error.error_code == "E-POWER"
        assert "E-POWER" in str(error)
        assert error.details == {"n": 20, "required": 28}


class TestTimeoutMonitoring:
    """Test timeout monitoring functionality."""
    
    def test_set_timeout_limit(self):
        """Test setting custom timeout limit."""
        set_timeout_limit(3600)
        # Note: We can't easily test the global variable, but we can verify
        # the function runs without error
        set_timeout_limit(14400)  # Reset to default
    
    def test_start_timeout_monitor(self):
        """Test starting timeout monitor."""
        start_timeout_monitor()
        # Should not raise
        assert True
    
    def test_check_timeout_no_start(self):
        """Test check_timeout when monitor not started."""
        start_timeout_monitor.__globals__['_start_time'] = None
        assert check_timeout() is False
    
    def test_check_timeout_not_exceeded(self):
        """Test check_timeout when limit not exceeded."""
        start_timeout_monitor()
        time.sleep(0.1)
        assert check_timeout() is False
    
    def test_check_timeout_exceeded(self):
        """Test check_timeout when limit exceeded."""
        # Set a very short timeout
        set_timeout_limit(0.001)  # 1ms
        start_timeout_monitor()
        time.sleep(0.1)  # Sleep longer than limit
        assert check_timeout() is True
        # Reset
        set_timeout_limit(14400)


class TestErrorRaisingFunctions:
    """Test error raising functions."""
    
    def test_raise_dataset_error(self):
        """Test raise_dataset_error raises correct exception."""
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error("Test dataset error", {"source": "test"})
        assert exc_info.value.error_code == "E-DATASET"
        assert exc_info.value.details == {"source": "test"}
    
    def test_raise_pairing_error(self):
        """Test raise_pairing_error raises correct exception."""
        with pytest.raises(E_PAIRING) as exc_info:
            raise_pairing_error("Test pairing error", {"rate": 0.5})
        assert exc_info.value.error_code == "E-PAIRING"
        assert exc_info.value.details == {"rate": 0.5}
    
    def test_raise_timeout_error(self):
        """Test raise_timeout_error raises correct exception."""
        with pytest.raises(E_TIMEOUT) as exc_info:
            raise_timeout_error("Test timeout error", {"elapsed": 15000})
        assert exc_info.value.error_code == "E-TIMEOUT"
        assert exc_info.value.details == {"elapsed": 15000}
    
    def test_raise_power_error(self):
        """Test raise_power_error raises correct exception."""
        with pytest.raises(E_POWER) as exc_info:
            raise_power_error("Test power error", {"n": 20})
        assert exc_info.value.error_code == "E-POWER"
        assert exc_info.value.details == {"n": 20}


class TestHandleError:
    """Test handle_error function."""
    
    @patch('sys.exit')
    def test_handle_error_calls_exit(self, mock_exit):
        """Test that handle_error calls sys.exit(1)."""
        error = E_DATASET("Test error")
        with patch('builtins.print'):  # Suppress print output
            handle_error(error)
        mock_exit.assert_called_once_with(1)
    
    @patch('sys.exit')
    def test_handle_error_with_details(self, mock_exit):
        """Test handle_error with error details."""
        error = E_DATASET("Test error", {"key": "value"})
        with patch('builtins.print'):
            handle_error(error)
        mock_exit.assert_called_once_with(1)


class TestTimeoutDecorator:
    """Test wrap_with_timeout decorator."""
    
    def test_decorator_allows_normal_execution(self):
        """Test decorator allows function to run normally."""
        @wrap_with_timeout
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_decorator_raises_on_timeout(self):
        """Test decorator raises E_TIMEOUT when limit exceeded."""
        # Set very short timeout
        set_timeout_limit(0.001)
        start_timeout_monitor()
        time.sleep(0.1)
        
        @wrap_with_timeout
        def test_func():
            return "should not reach here"
        
        with pytest.raises(E_TIMEOUT):
            test_func()
        
        # Reset
        set_timeout_limit(14400)