"""
Unit tests for the error handling framework.

Tests verify that:
1. All error codes (E_DATASET, E_PAIRING, E_TIMEOUT, E_POWER) are properly defined
2. Errors raise with correct attributes and exit behavior
3. Validation functions correctly trigger errors when thresholds are not met
4. Timeout monitoring works as expected
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
import time

# Import the error handling modules
from code.exceptions import (
    PipelineError, E_DATASET, E_PAIRING, E_TIMEOUT, E_POWER, E_SAMPLESIZE,
    raise_dataset_error, raise_pairing_error, raise_timeout_error,
    raise_power_error, raise_samplesize_error
)
from code.error_handler import (
    set_timeout_limit, start_timeout_monitor, check_timeout,
    validate_pairing_rate, validate_sample_size, wrap_with_timeout
)


class TestPipelineError:
    """Tests for the base PipelineError class."""
    
    def test_base_error_initialization(self):
        """Test that PipelineError initializes correctly with all attributes."""
        error = PipelineError("Test message", "TEST_CODE", {"key": "value"})
        
        assert error.message == "Test message"
        assert error.error_code == "TEST_CODE"
        assert error.details == {"key": "value"}
        assert str(error) == "Test message"
    
    def test_base_error_without_details(self):
        """Test that PipelineError works without details."""
        error = PipelineError("Test message", "TEST_CODE")
        
        assert error.details == {}
        assert error.error_code == "TEST_CODE"
    
    def test_error_logging_on_creation(self):
        """Test that errors log when created."""
        with patch('code.exceptions.logging.getLogger') as mock_logger:
            error = PipelineError("Test message", "TEST_CODE")
            mock_logger.return_value.error.assert_called_once()


class TestSpecificErrors:
    """Tests for specific error types."""
    
    def test_e_dataset_error(self):
        """Test E_DATASET error initialization and attributes."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                error = E_DATASET("Dataset not found", {"source": "GEO"})
                
                assert error.error_code == "E_DATASET"
                assert error.message == "Dataset not found"
                assert error.details == {"source": "GEO"}
    
    def test_e_pairing_error(self):
        """Test E_PAIRING error initialization and attributes."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                error = E_PAIRING("Pairing rate too low", {"rate": 0.80})
                
                assert error.error_code == "E_PAIRING"
                assert error.message == "Pairing rate too low"
                assert error.details == {"rate": 0.80}
    
    def test_e_timeout_error(self):
        """Test E_TIMEOUT error initialization and attributes."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                error = E_TIMEOUT("Execution time exceeded", {"elapsed": 15000})
                
                assert error.error_code == "E_TIMEOUT"
                assert error.message == "Execution time exceeded"
                assert error.details == {"elapsed": 15000}
    
    def test_e_power_error(self):
        """Test E_POWER error initialization and attributes."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                error = E_POWER("Insufficient power", {"n": 20, "required": 28})
                
                assert error.error_code == "E_POWER"
                assert error.message == "Insufficient power"
                assert error.details == {"n": 20, "required": 28}
    
    def test_e_samplesize_error(self):
        """Test E_SAMPLESIZE error initialization and attributes."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                error = E_SAMPLESIZE("Sample size too small", {"n": 30, "required": 50})
                
                assert error.error_code == "E_SAMPLESIZE"
                assert error.message == "Sample size too small"
                assert error.details == {"n": 30, "required": 50}

class TestErrorFunctions:
    """Tests for error raising functions."""
    
    def test_raise_dataset_error(self):
        """Test that raise_dataset_error raises E_DATASET."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                with pytest.raises(E_DATASET) as exc_info:
                    raise_dataset_error("Test error", {"detail": "value"})
                
                assert exc_info.value.error_code == "E_DATASET"
                assert exc_info.value.details == {"detail": "value"}
    
    def test_raise_pairing_error(self):
        """Test that raise_pairing_error raises E_PAIRING."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                with pytest.raises(E_PAIRING) as exc_info:
                    raise_pairing_error("Test error")
                
                assert exc_info.value.error_code == "E_PAIRING"
    
    def test_raise_timeout_error(self):
        """Test that raise_timeout_error raises E_TIMEOUT."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                with pytest.raises(E_TIMEOUT) as exc_info:
                    raise_timeout_error("Test error")
                
                assert exc_info.value.error_code == "E_TIMEOUT"
    
    def test_raise_power_error(self):
        """Test that raise_power_error raises E_POWER."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                with pytest.raises(E_POWER) as exc_info:
                    raise_power_error("Test error")
                
                assert exc_info.value.error_code == "E_POWER"
    
    def test_raise_samplesize_error(self):
        """Test that raise_samplesize_error raises E_SAMPLESIZE."""
        with patch('sys.exit'):
            with patch('code.exceptions.logging.getLogger'):
                with pytest.raises(E_SAMPLESIZE) as exc_info:
                    raise_samplesize_error("Test error")
                
                assert exc_info.value.error_code == "E_SAMPLESIZE"

class TestValidationFunctions:
    """Tests for validation utility functions."""
    
    def test_validate_pairing_rate_success(self):
        """Test that validation passes when rate is above threshold."""
        # Should not raise
        validate_pairing_rate(0.96, 0.95)
        validate_pairing_rate(1.0, 0.95)
    
    def test_validate_pairing_rate_failure(self):
        """Test that validation raises E_PAIRING when rate is below threshold."""
        with patch('code.error_handler.logging.getLogger'):
            with pytest.raises(E_PAIRING):
                validate_pairing_rate(0.90, 0.95)
    
    def test_validate_pairing_rate_exact_threshold(self):
        """Test that validation passes at exactly the threshold."""
        validate_pairing_rate(0.95, 0.95)
    
    def test_validate_sample_size_success(self):
        """Test that sample size validation passes when size is sufficient."""
        # Should not raise
        validate_sample_size(30, 28, "power")
        validate_sample_size(50, 50, "cross_species")
    
    def test_validate_sample_size_power_failure(self):
        """Test that E_POWER is raised for insufficient power sample size."""
        with patch('code.error_handler.logging.getLogger'):
            with pytest.raises(E_POWER):
                validate_sample_size(20, 28, "power")
    
    def test_validate_sample_size_specific_failure(self):
        """Test that E_SAMPLESIZE is raised for specific analysis failure."""
        with patch('code.error_handler.logging.getLogger'):
            with pytest.raises(E_SAMPLESIZE):
                validate_sample_size(40, 50, "cross_species")

class TestTimeoutFunctions:
    """Tests for timeout monitoring functions."""
    
    def test_set_timeout_limit(self):
        """Test setting timeout limit."""
        set_timeout_limit(100)
        # Reset to default after test
        set_timeout_limit(4 * 60 * 60)
    
    def test_start_timeout_monitor(self):
        """Test starting timeout monitor."""
        start_timeout_monitor()
        # Should set _timeout_start_time
        # We can't easily verify the global state, but no exception means it worked
    
    def test_check_timeout_no_timeout(self):
        """Test that check_timeout returns False when not timed out."""
        start_timeout_monitor()
        # Immediately check - should not timeout
        result = check_timeout()
        assert result is False
    
    def test_wrap_with_timeout(self):
        """Test the timeout wrapper decorator."""
        @wrap_with_timeout
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_wrap_with_timeout_timeout_exceeded(self):
        """Test that wrapper raises E_TIMEOUT when limit exceeded."""
        # Set a very short timeout
        set_timeout_limit(0.001)  # 1ms
        
        @wrap_with_timeout
        def slow_func():
            time.sleep(0.1)  # Sleep longer than timeout
            return "success"
        
        with patch('code.error_handler.logging.getLogger'):
            with pytest.raises(E_TIMEOUT):
                slow_func()
        
        # Reset timeout
        set_timeout_limit(4 * 60 * 60)