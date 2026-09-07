"""
Unit tests for logger.py infrastructure.

Verifies:
- Logger initialization and configuration
- Error logging functionality
- Exception hierarchy
- File handler creation
"""
import logging
import pytest
import tempfile
import time
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import (
    setup_logger,
    log_error,
    safe_execute,
    ResearchError,
    DataLoadError,
    ModelExecutionError,
    ConfigurationError,
    AnalysisError
)


class TestLoggerSetup:
    """Tests for setup_logger() function."""
    
    def test_logger_initialization(self):
        """Test that logger is properly initialized with default settings."""
        logger = setup_logger("test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO  # Default level
        assert len(logger.handlers) > 0  # Should have at least console handler
        
    def test_logger_custom_level(self):
        """Test logger with custom log level."""
        logger = setup_logger("test_logger_debug", level="DEBUG")
        
        assert logger.level == logging.DEBUG
        
    def test_logger_file_handler(self):
        """Test logger creates file handler when log_file is specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger("test_file_logger", log_file="test.log", console=False)
            
            # Check that file was created
            assert log_path.exists()
            
            # Check that file handler exists
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
            
    def test_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger multiple times doesn't duplicate handlers."""
        logger = setup_logger("test_duplicate")
        initial_count = len(logger.handlers)
        
        # Call again
        logger2 = setup_logger("test_duplicate")
        
        assert len(logger2.handlers) == initial_count
        assert len(logger2.handlers) == 1  # Should still be just console handler
        
    def test_logger_formatter(self):
        """Test that logger has proper formatter."""
        logger = setup_logger("test_formatter")
        
        for handler in logger.handlers:
            assert handler.formatter is not None
            # Check format includes timestamp, level, and message
            format_str = handler.formatter._fmt
            assert "asctime" in format_str
            assert "levelname" in format_str
            assert "message" in format_str


class TestExceptionHierarchy:
    """Tests for custom exception classes."""
    
    def test_research_error_base(self):
        """Test base ResearchError."""
        error = ResearchError("Test message", context={"key": "value"})
        
        assert error.message == "Test message"
        assert error.context == {"key": "value"}
        assert error.timestamp is not None
        assert isinstance(error, Exception)
        
    def test_data_load_error(self):
        """Test DataLoadError subclass."""
        error = DataLoadError("Failed to load data", context={"file": "data.csv"})
        
        assert isinstance(error, ResearchError)
        assert isinstance(error, DataLoadError)
        assert error.context == {"file": "data.csv"}
        
    def test_model_execution_error(self):
        """Test ModelExecutionError subclass."""
        error = ModelExecutionError("Model failed", context={"model": "llama-7b"})
        
        assert isinstance(error, ResearchError)
        assert isinstance(error, ModelExecutionError)
        
    def test_configuration_error(self):
        """Test ConfigurationError subclass."""
        error = ConfigurationError("Invalid config", context={"param": "value"})
        
        assert isinstance(error, ResearchError)
        assert isinstance(error, ConfigurationError)
        
    def test_analysis_error(self):
        """Test AnalysisError subclass."""
        error = AnalysisError("Analysis failed", context={"test": "case"})
        
        assert isinstance(error, ResearchError)
        assert isinstance(error, AnalysisError)


class TestSafeExecute:
    """Tests for safe_execute() function."""
    
    def test_successful_execution(self):
        """Test safe_execute with successful function."""
        def success_func():
            return "success"
        
        result = safe_execute(success_func)
        assert result == "success"
        
    def test_failed_execution_raises(self):
        """Test safe_execute raises ResearchError on failure."""
        def fail_func():
            raise ValueError("Something went wrong")
        
        with pytest.raises(ResearchError):
            safe_execute(fail_func)
            
    def test_failed_execution_with_logger(self):
        """Test safe_execute logs error when using provided logger."""
        def fail_func():
            raise ValueError("Test error")
        
        logger = setup_logger("test_safe_execute", console=False)
        
        with pytest.raises(ResearchError):
            safe_execute(fail_func, logger=logger)
            
    def test_research_error_passthrough(self):
        """Test that ResearchErrors are re-raised with context preserved."""
        def fail_func():
            raise DataLoadError("Data load failed", context={"file": "test.csv"})
        
        with pytest.raises(DataLoadError) as exc_info:
            safe_execute(fail_func)
            
        assert exc_info.value.context == {"file": "test.csv"}


class TestLogErrorAndRaise:
    """Tests for log_error() function."""
    
    def test_log_error_basic(self):
        """Test basic error logging."""
        logger = setup_logger("test_log_error", console=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger("test_log_error_file", log_file="test.log", console=False)
            
            error = ValueError("Test error")
            
            # Should not raise
            log_error(logger, error, should_raise=False)
            
            # Check log file contains error
            assert log_path.exists()
            content = log_path.read_text()
            assert "Test error" in content
            assert "ERROR" in content
            
    def test_log_error_with_context(self):
        """Test error logging with context."""
        logger = setup_logger("test_log_context", console=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger("test_log_context_file", log_file="test.log", console=False)
            
            error = ValueError("Test error")
            context = {"instance_id": 42, "strategy": "tfidf"}
            
            log_error(logger, error, context=context, should_raise=False)
            
            content = log_path.read_text()
            assert "instance_id=42" in content
            assert "strategy=tfidf" in content
            
    def test_log_error_with_message(self):
        """Test error logging with custom message."""
        logger = setup_logger("test_log_msg", console=False)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = setup_logger("test_log_msg_file", log_file="test.log", console=False)
            
            error = ValueError("Original error")
            
            log_error(logger, error, message="Custom message", should_raise=False)
            
            content = log_path.read_text()
            assert "Custom message" in content
            assert "Original error" in content
            
    def test_log_error_raises(self):
        """Test that log_error re-raises when should_raise=True."""
        logger = setup_logger("test_log_raise", console=False)
        
        error = ValueError("Test error")
        
        with pytest.raises(ValueError):
            log_error(logger, error, should_raise=True)


class TestRootLogger:
    """Tests for root logger behavior."""
    
    def test_root_logger_not_modified(self):
        """Test that setup_logger doesn't modify root logger."""
        root_handlers_before = len(logging.root.handlers)
        
        logger = setup_logger("test_root")
        
        root_handlers_after = len(logging.root.handlers)
        
        assert root_handlers_before == root_handlers_after