"""
Unit tests for the error handling framework.

Tests verify that:
- Custom exceptions are raised with correct error codes
- Error messages are properly formatted
- Timeout monitoring works correctly
"""

import pytest
import time
from pathlib import Path
import tempfile

from code.exceptions import (
    PipelineError,
    E_DATASET,
    E_PAIRING,
    E_TIMEOUT,
    E_POWER
)
from code.error_handler import (
    handle_error,
    raise_dataset_error,
    raise_pairing_error,
    raise_timeout_error,
    raise_power_error,
    check_timeout,
    start_timeout_monitor,
    set_timeout_limit
)

class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_pipeline_error_base(self):
        """Test base PipelineError."""
        exc = PipelineError("Test message", "E-TEST")
        assert exc.message == "Test message"
        assert exc.error_code == "E-TEST"
        assert "[E-TEST]" in str(exc)
    
    def test_e_dataset(self):
        """Test E_DATASET exception."""
        exc = E_DATASET("No data found")
        assert exc.error_code == "E-DATASET"
        assert "[E-DATASET] No data found" in str(exc)
    
    def test_e_pairing(self):
        """Test E_PAIRING exception."""
        exc = E_PAIRING("Pairing rate too low")
        assert exc.error_code == "E-PAIRING"
        assert "[E-PAIRING] Pairing rate too low" in str(exc)
    
    def test_e_timeout(self):
        """Test E_TIMEOUT exception."""
        exc = E_TIMEOUT("Time limit exceeded")
        assert exc.error_code == "E-TIMEOUT"
        assert "[E-TIMEOUT] Time limit exceeded" in str(exc)
    
    def test_e_power(self):
        """Test E_POWER exception."""
        exc = E_POWER("Insufficient sample size")
        assert exc.error_code == "E-POWER"
        assert "[E-POWER] Insufficient sample size" in str(exc)

class TestErrorRaisingFunctions:
    """Test functions that raise specific errors."""
    
    def test_raise_dataset_error(self):
        """Test raise_dataset_error raises E_DATASET."""
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error("GEO search failed")
        assert exc_info.value.error_code == "E-DATASET"
    
    def test_raise_dataset_error_with_context(self):
        """Test raise_dataset_error with context dict."""
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error("Accession not found", {"accession": "GSE12345"})
        assert exc_info.value.error_code == "E-DATASET"
        assert "accession=GSE12345" in str(exc_info.value)
    
    def test_raise_pairing_error(self):
        """Test raise_pairing_error raises E_PAIRING."""
        with pytest.raises(E_PAIRING) as exc_info:
            raise_pairing_error("Pairing rate 80%")
        assert exc_info.value.error_code == "E-PAIRING"
    
    def test_raise_power_error(self):
        """Test raise_power_error raises E_POWER."""
        with pytest.raises(E_POWER) as exc_info:
            raise_power_error("n=15 < 28 required")
        assert exc_info.value.error_code == "E-POWER"
    
    def test_raise_timeout_error(self):
        """Test raise_timeout_error raises E_TIMEOUT."""
        with pytest.raises(E_TIMEOUT) as exc_info:
            raise_timeout_error("Pipeline took too long")
        assert exc_info.value.error_code == "E-TIMEOUT"

class TestHandleError:
    """Test centralized error handler."""
    
    def test_handle_error_logs_and_exits(self, caplog):
        """Test handle_error logs the error and exits."""
        exc = E_DATASET("Test error")
        with pytest.raises(SystemExit) as exc_info:
            with caplog.at_level("CRITICAL"):
                handle_error(exc, exit_on_error=True)
        assert exc_info.value.code == 1
        assert "E-DATASET" in caplog.text
    
    def test_handle_error_to_file(self):
        """Test handle_error writes to log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_path = Path(f.name)
        
        exc = E_PAIRING("Test pairing error")
        with pytest.raises(SystemExit):
            handle_error(exc, log_file=log_path, exit_on_error=True)
        
        # Verify file content
        content = log_path.read_text()
        assert "E-PAIRING" in content
        assert "Test pairing error" in content
        
        log_path.unlink()

class TestTimeoutMonitoring:
    """Test timeout monitoring functionality."""
    
    def test_timeout_monitor_start(self):
        """Test that timeout monitor starts correctly."""
        start_timeout_monitor()
        # Should not raise
        assert check_timeout() is False
    
    def test_timeout_check_within_limit(self):
        """Test check_timeout returns False within limit."""
        set_timeout_limit(3600)  # 1 hour
        start_timeout_monitor()
        # Immediately check - should be well within limit
        assert check_timeout() is False
    
    def test_timeout_check_exceeds_limit(self):
        """Test check_timeout returns True when exceeded."""
        # Set a very short limit for testing
        set_timeout_limit(0)  # 0 seconds
        start_timeout_monitor()
        time.sleep(0.01)  # Small delay
        assert check_timeout() is True
    
    def test_timeout_without_start(self):
        """Test check_timeout returns False if not started."""
        # Reset start time
        import code.error_handler as handler
        handler._start_time = None
        assert check_timeout() is False