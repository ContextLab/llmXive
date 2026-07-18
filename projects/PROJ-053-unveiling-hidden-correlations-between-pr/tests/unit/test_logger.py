"""
Unit tests for the logging infrastructure.
"""
import logging
import tempfile
import os
from pathlib import Path
import pytest

# Mock the config to use temporary directories for testing
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# We need to test the logger module, but we need to ensure config is mocked
# because get_project_root might fail in test environment if contracts/ doesn't exist


@pytest.fixture
def mock_config():
    """Mock the config module to avoid path issues in tests."""
    with patch('config.get_project_root') as mock_root, \
         patch('config.get_logs_dir') as mock_logs, \
         patch('config.ensure_directories') as mock_ensure:

        # Create a temporary directory for logs
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_root.return_value = Path(tmpdir)
            mock_logs.return_value = Path(tmpdir) / "logs"
            mock_ensure.return_value = None

            # Clear the global logger cache in config
            import config
            config._logger = None

            yield mock_root, mock_logs, mock_ensure


def test_setup_logging_creates_logger(mock_config):
    """Test that setup_logging returns a valid logger."""
    from utils.logger import setup_logging

    logger = setup_logging()

    assert logger is not None
    assert isinstance(logger, logging.Logger)
    assert logger.name == "llmXive"


def test_setup_logging_sets_level(mock_config):
    """Test that setup_logging respects log_level parameter."""
    from utils.logger import setup_logging

    logger = setup_logging(log_level=logging.DEBUG)
    assert logger.level == logging.DEBUG

    logger2 = setup_logging(log_level=logging.WARNING)
    assert logger2.level == logging.WARNING


def test_log_execution_time_success(mock_config, caplog):
    """Test that log_execution_time logs start and end times on success."""
    from utils.logger import log_execution_time
    import logging

    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)

    with caplog.at_level(logging.INFO):
        with log_execution_time(logger, "Test Operation"):
            pass

    assert "Starting Test Operation" in caplog.text
    assert "Completed Test Operation" in caplog.text


def test_log_execution_time_failure(mock_config, caplog):
    """Test that log_execution_time logs error on exception."""
    from utils.logger import log_execution_time
    import logging

    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.ERROR)

    with pytest.raises(ValueError):
        with caplog.at_level(logging.ERROR):
            with log_execution_time(logger, "Failing Operation"):
                raise ValueError("Test error")

    assert "Failing Operation failed" in caplog.text


def test_log_error_and_raise(mock_config, caplog):
    """Test that log_error_and_raise logs and raises."""
    from utils.logger import log_error_and_raise
    import logging

    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.ERROR)

    with pytest.raises(RuntimeError):
        with caplog.at_level(logging.ERROR):
            log_error_and_raise(logger, "Test error message")

    assert "Test error message" in caplog.text


def test_get_log_file_path(mock_config):
    """Test that get_log_file_path returns the correct path."""
    from utils.logger import get_log_file_path
    from pathlib import Path

    path = get_log_file_path()
    assert isinstance(path, Path)
    assert path.name == "pipeline.log"
