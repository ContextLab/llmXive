"""
Unit tests for src/utils/logger.py.
"""

import logging
import tempfile
import os
from pathlib import Path
import pytest

from src.utils.logger import get_logger, _get_config_path


@pytest.fixture
def temp_logging_conf():
    """Create a temporary logging.conf file for testing."""
    conf_content = """
    [loggers]
    keys=root,llmXive

    [handlers]
    keys=consoleHandler,fileHandler

    [formatters]
    keys=simpleFormatter

    [logger_root]
    level=WARNING
    handlers=consoleHandler

    [logger_llmXive]
    level=INFO
    handlers=consoleHandler
    qualname=llmXive
    propagate=0

    [handler_consoleHandler]
    class=StreamHandler
    level=INFO
    formatter=simpleFormatter
    args=(sys.stdout,)

    [handler_fileHandler]
    class=FileHandler
    level=DEBUG
    formatter=simpleFormatter
    args=('test_pipeline.log',)

    [formatter_simpleFormatter]
    format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        conf_path = Path(tmpdir) / "logging.conf"
        conf_path.write_text(conf_content)
        # Temporarily change CWD to the temp directory so _get_config_path finds it
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            yield conf_path
        finally:
            os.chdir(original_cwd)


def test_get_logger_returns_instance(temp_logging_conf):
    """Test that get_logger returns a valid Logger instance."""
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "llmXive"


def test_get_logger_with_custom_name(temp_logging_conf):
    """Test that get_logger respects the name argument."""
    custom_name = "custom_test_logger"
    logger = get_logger(name=custom_name)
    assert isinstance(logger, logging.Logger)
    assert logger.name == custom_name


def test_get_logger_configured_correctly(temp_logging_conf):
    """Test that the logger has the expected level and handlers."""
    logger = get_logger()
    # Based on the temp conf, llmXive logger level is INFO
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_get_logger_reuses_existing_instance(temp_logging_conf):
    """Test that calling get_logger multiple times returns the same configured logger."""
    logger1 = get_logger("reuse_test")
    logger2 = get_logger("reuse_test")
    assert logger1 is logger2