"""
Unit tests for the main.py logging and error handling infrastructure.
"""

import logging
import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Ensure code/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.main import (
    setup_logging,
    handle_critical_error,
    validate_environment,
    main
)


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_console_only(self, caplog):
        """Test logging to console only."""
        logger = setup_logging(log_level="INFO", enable_file=False)
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        assert "Test message" in caplog.text

    def test_setup_logging_invalid_level(self):
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError):
            setup_logging(log_level="INVALID")

    def test_setup_logging_file_handler(self):
        """Test logging to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_level="INFO", log_file=log_file)
            
            logger.info("File test message")
            
            # Check file exists and contains message
            assert os.path.exists(log_file)
            with open(log_file, 'r') as f:
                content = f.read()
            assert "File test message" in content

    def test_setup_logging_missing_directory(self):
        """Test that missing log directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            setup_logging(log_file="/nonexistent/dir/test.log")

    def test_setup_logging_duplicate_handlers(self):
        """Test that re-calling setup_logging doesn't duplicate handlers."""
        logger = setup_logging(log_level="INFO", enable_console=False)
        initial_count = len(logger.handlers)
        
        # Call again with same settings
        logger2 = setup_logging(log_level="INFO", enable_console=False)
        assert len(logger2.handlers) == initial_count


class TestHandleCriticalError:
    """Tests for the handle_critical_error function."""

    def test_handle_error_logs_context(self, caplog):
        """Test that context is logged correctly."""
        logger = setup_logging(log_level="CRITICAL", enable_file=False)
        
        with caplog.at_level(logging.CRITICAL):
            handle_critical_error(
                Exception("Test error"),
                context={"task": "test", "value": 123},
                logger=logger,
                exit_on_error=False
            )
        
        assert "Context[task]: test" in caplog.text
        assert "Context[value]: 123" in caplog.text
        assert "Exception Type: Exception" in caplog.text
        assert "Test error" in caplog.text

    def test_handle_error_logs_traceback(self, caplog):
        """Test that traceback is logged."""
        logger = setup_logging(log_level="CRITICAL", enable_file=False)
        
        try:
            1 / 0
        except Exception as e:
            with caplog.at_level(logging.CRITICAL):
                handle_critical_error(
                    e,
                    context={},
                    logger=logger,
                    exit_on_error=False
                )
        
        assert "Traceback:" in caplog.text
        assert "ZeroDivisionError" in caplog.text

    @patch('code.main.sys.exit')
    def test_handle_error_exits(self, mock_exit, caplog):
        """Test that function calls sys.exit on error."""
        logger = setup_logging(log_level="CRITICAL", enable_file=False)
        
        with caplog.at_level(logging.CRITICAL):
            handle_critical_error(
                Exception("Exit test"),
                context={},
                logger=logger,
                exit_on_error=True
            )
        
        mock_exit.assert_called_once_with(1)

    def test_handle_error_creates_logger_if_none(self, caplog):
        """Test that a logger is created if none provided."""
        with caplog.at_level(logging.CRITICAL):
            handle_critical_error(
                Exception("No logger test"),
                context={},
                logger=None,
                exit_on_error=False
            )
        
        assert "No logger test" in caplog.text


class TestValidateEnvironment:
    """Tests for the validate_environment function."""

    def test_validate_environment_returns_dict(self):
        """Test that function returns a dictionary."""
        result = validate_environment()
        assert isinstance(result, dict)

    def test_validate_environment_contains_expected_keys(self):
        """Test that result contains expected dependency keys."""
        result = validate_environment()
        expected_keys = ["python_version", "numpy", "pandas", "torch", "datasets", "xgboost"]
        for key in expected_keys:
            assert key in result

    def test_validate_environment_values_are_bool(self):
        """Test that all values in result are booleans."""
        result = validate_environment()
        for value in result.values():
            assert isinstance(value, bool)

    def test_validate_environment_python_version(self):
        """Test that python_version is True for Python 3.10+."""
        result = validate_environment()
        # Assuming the runner is on Python 3.11 as per project specs
        assert result["python_version"] is True


class TestMain:
    """Tests for the main entry point function."""

    @patch('code.main.validate_environment')
    @patch('code.main.setup_logging')
    def test_main_success(self, mock_setup_log, mock_validate):
        """Test main returns 0 on success."""
        mock_setup_log.return_value = MagicMock()
        mock_validate.return_value = {
            "python_version": True,
            "numpy": True,
            "pandas": True,
            "torch": True,
            "datasets": True,
            "xgboost": True
        }
        
        with patch('code.main.sys.exit') as mock_exit:
            result = main()
            assert result == 0
            mock_exit.assert_not_called()

    @patch('code.main.handle_critical_error')
    @patch('code.main.validate_environment')
    @patch('code.main.setup_logging')
    def test_main_failure_missing_deps(self, mock_setup_log, mock_validate, mock_handle):
        """Test main handles missing dependencies."""
        mock_setup_log.return_value = MagicMock()
        mock_validate.return_value = {
            "python_version": True,
            "numpy": False,
            "pandas": True,
            "torch": True,
            "datasets": True,
            "xgboost": True
        }
        
        result = main()
        # Should return 1 or exit
        assert result == 1
        mock_handle.assert_called_once()