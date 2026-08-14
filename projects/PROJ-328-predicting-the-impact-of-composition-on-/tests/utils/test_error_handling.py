"""
Tests for the error handling and logging infrastructure.
"""
import pytest
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
code_path = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from utils.error_handlers import (
    SolderPipelineError,
    ConfigurationError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    DataInsufficientError,
    CompositionSumError,
    log_error
)
from utils.logging_config import setup_logging, get_logger, init_project_logger

class TestSolderPipelineError:
    def test_base_error_creation(self):
        error = SolderPipelineError("Test message")
        assert error.message == "Test message"
        assert error.context == {}

    def test_base_error_with_context(self):
        context = {"key": "value"}
        error = SolderPipelineError("Test message", context=context)
        assert error.context == context

    def test_subclass_inheritance(self):
        error = ConfigurationError("Config failed")
        assert isinstance(error, SolderPipelineError)
        
        error = DataValidationError("Data bad")
        assert isinstance(error, SolderPipelineError)
        
        error = IngestionError("Fetch failed")
        assert isinstance(error, SolderPipelineError)
        
        error = ModelTrainingError("Training failed")
        assert isinstance(error, SolderPipelineError)
        
        error = DataInsufficientError("Data too small")
        assert isinstance(error, SolderPipelineError)
        
        error = CompositionSumError("Sum bad")
        assert isinstance(error, SolderPipelineError)

class TestLoggingConfig:
    def test_setup_logging_creates_handlers(self, tmp_path):
        # Mock the log directory to use a temp path
        with patch('utils.logging_config._LOG_DIR', tmp_path):
            with patch('utils.logging_config._logging_setup', False):
                with patch('utils.logging_config._loggers', {}):
                    setup_logging(enable_console_logging=False, enable_file_logging=True)
                    
                    root_logger = logging.getLogger()
                    assert len(root_logger.handlers) >= 1
                    
                    # Check if file handler exists
                    file_handler_found = False
                    for handler in root_logger.handlers:
                        if isinstance(handler, logging.FileHandler):
                            file_handler_found = True
                            break
                    assert file_handler_found

    def test_get_logger_returns_instance(self):
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_init_project_logger(self):
        logger = init_project_logger()
        assert isinstance(logger, logging.Logger)

class TestLogError:
    def test_log_error_function(self, caplog):
        caplog.set_level(logging.ERROR)
        error = ConfigurationError("Test config error")
        log_error(error, level=logging.ERROR)
        
        assert "Test config error" in caplog.text
        assert "ConfigurationError" in caplog.text
