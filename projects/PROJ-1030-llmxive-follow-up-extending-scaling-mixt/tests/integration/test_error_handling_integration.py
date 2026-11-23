import pytest
import time
from pathlib import Path
from utils.error_handler import retry_with_backoff, DataFetchError, ConfigError
from utils.logging_config import get_logger, fail_loudly
from utils.config_manager import initialize_project_config

class TestErrorHandlingIntegration:
    """Integration tests for error handling infrastructure."""

    def test_retry_with_backoff_integration(self):
        """Test retry mechanism with realistic delays."""
        call_times = []
        
        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.1,
            max_delay=0.5,
            backoff_factor=2.0
        )
        def flaky_fetch():
            call_times.append(time.time())
            if len(call_times) < 2:
                raise ConnectionError("Network timeout")
            return "data"
        
        result = flaky_fetch()
        assert result == "data"
        assert len(call_times) == 2
        
        # Verify exponential backoff (roughly)
        delay = call_times[1] - call_times[0]
        assert delay >= 0.05  # Allow some tolerance

    def test_fail_loudly_integration(self):
        """Test that fail_loudly properly logs and exits."""
        logger = get_logger("integration_test")
        
        # This should exit, so we test it in a way that catches the exit
        with pytest.raises(SystemExit):
            fail_loudly(logger, "Integration test failure", error_code=3)

    def test_config_validation_integration(self):
        """Test config validation with missing keys."""
        config = initialize_project_config()
        
        # Verify config has required attributes
        assert hasattr(config, 'project_root')
        assert hasattr(config, 'data_dir')
        assert hasattr(config, 'max_memory_gb')
        
        # Verify directories exist
        assert config.project_root.exists()

    def test_error_logging_to_file(self):
        """Test that errors are logged to file."""
        import logging
        from utils.logging_config import LOGS_DIR
        
        logger = get_logger("file_test")
        
        with pytest.raises(SystemExit):
            fail_loudly(logger, "Test file logging error")
        
        # Check that log file exists and contains error
        log_file = LOGS_DIR / "pipeline.log"
        assert log_file.exists()
        
        content = log_file.read_text()
        assert "FATAL ERROR" in content
        assert "Test file logging error" in content

    def test_data_fetch_error_propagation(self):
        """Test that DataFetchError propagates correctly."""
        @retry_with_backoff(max_retries=1, initial_delay=0.01)
        def failing_fetch():
            raise DataFetchError("Failed to fetch from API")
        
        with pytest.raises(SystemExit):
            failing_fetch()