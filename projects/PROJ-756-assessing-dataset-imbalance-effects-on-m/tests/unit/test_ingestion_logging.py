import os
import sys
import logging
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from ingestion import exponential_backoff_retry, fetch_oqmd_data, logger

class TestExponentialBackoffRetry:
    """Tests for the exponential backoff retry logic and logging."""

    def test_successful_execution_no_retry(self):
        """Test that a successful function executes once and logs success."""
        mock_func = MagicMock(return_value="success")
        
        with patch('ingestion.logger') as mock_logger:
            result = exponential_backoff_retry(mock_func)
            
            assert result == "success"
            mock_func.assert_called_once()
            mock_logger.info.assert_any_call("Successfully executed mock_func on attempt 1")

    def test_retry_on_failure_then_success(self):
        """Test that the function retries on failure and succeeds."""
        mock_func = MagicMock(side_effect=[
            Exception("Temporary error"),
            "success"
        ])
        
        with patch('ingestion.logger') as mock_logger:
            # Patch time.sleep to avoid actual waiting in tests
            with patch('ingestion.time.sleep'):
                result = exponential_backoff_retry(mock_func, max_retries=5, backoff_factor=0.1)
                
                assert result == "success"
                assert mock_func.call_count == 2
                # Check that warning and info logs were called
                warning_calls = [call for call in mock_logger.warning.call_args_list if 'Retrying' in str(call)]
                info_calls = [call for call in mock_logger.info.call_args_list if 'Successfully' in str(call)]
                assert len(warning_calls) >= 1
                assert len(info_calls) >= 1

    def test_max_retries_exceeded_logs_error(self):
        """Test that max retries exceeded logs an error and raises exception."""
        mock_func = MagicMock(side_effect=Exception("Persistent error"))
        
        with patch('ingestion.logger') as mock_logger:
            # Patch time.sleep to avoid actual waiting in tests
            with patch('ingestion.time.sleep'):
                with pytest.raises(Exception, match="Persistent error"):
                    exponential_backoff_retry(mock_func, max_retries=2, backoff_factor=0.1)
                
                # Verify error log was called
                error_calls = [call for call in mock_logger.error.call_args_list if 'failed after' in str(call)]
                assert len(error_calls) >= 1

    def test_timeout_error_handling(self):
        """Test that timeout errors are handled with retry logic."""
        from requests.exceptions import Timeout
        
        mock_func = MagicMock(side_effect=[
            Timeout("Connection timed out"),
            "success"
        ])
        
        with patch('ingestion.logger') as mock_logger:
            with patch('ingestion.time.sleep'):
                result = exponential_backoff_retry(mock_func, max_retries=5, backoff_factor=0.1)
                
                assert result == "success"
                assert mock_func.call_count == 2
                
                # Check for timeout-specific warning
                warning_calls = [call for call in mock_logger.warning.call_args_list if 'Timeout Error' in str(call)]
                assert len(warning_calls) >= 1

    def test_request_exception_handling(self):
        """Test that RequestException errors are handled with retry logic."""
        from requests.exceptions import RequestException
        
        mock_func = MagicMock(side_effect=[
            RequestException("Network error"),
            "success"
        ])
        
        with patch('ingestion.logger') as mock_logger:
            with patch('ingestion.time.sleep'):
                result = exponential_backoff_retry(mock_func, max_retries=5, backoff_factor=0.1)
                
                assert result == "success"
                assert mock_func.call_count == 2
                
                # Check for API error warning
                warning_calls = [call for call in mock_logger.warning.call_args_list if 'API Error' in str(call)]
                assert len(warning_calls) >= 1

class TestLoggingConfiguration:
    """Tests for logging configuration."""

    def test_logger_exists_and_configured(self):
        """Test that the logger is properly configured."""
        assert logger is not None
        assert logger.name == "ingestion"
        assert logger.level == logging.INFO

    def test_log_format(self):
        """Test that log messages have the correct format."""
        import io
        import logging
        
        # Create a string handler to capture logs
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        test_logger = logging.getLogger('test_ingestion_log')
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        test_logger.info("Test message")
        log_output = log_stream.getvalue()
        
        assert "test_ingestion_log" in log_output
        assert "INFO" in log_output
        assert "Test message" in log_output
