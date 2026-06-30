"""
Unit tests for logging configuration module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.logging_config import (
    get_logger,
    log_reproducibility_manifest,
    log_event,
    setup_logging,
    JSONFormatter,
    LOG_KEYS
)
import logging

class TestJSONFormatter:
    """Tests for JSONFormatter class."""
    
    def test_format_basic_log(self):
        """Test basic log formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
        assert parsed["module"] == "test"
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields."""
        formatter = JSONFormatter(extra_fields=["experiment_id", "seed"])
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.experiment_id = "exp_001"
        record.seed = 42
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["experiment_id"] == "exp_001"
        assert parsed["seed"] == 42

class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"
    
    def test_get_logger_custom_name(self):
        """Test getting logger with custom name."""
        logger = get_logger(name="custom_test")
        assert logger.name == "custom_test"
    
    def test_get_logger_singleton(self):
        """Test that get_logger returns same instance."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2

class TestLogReproducibilityManifest:
    """Tests for log_reproducibility_manifest function."""
    
    def test_manifest_creation(self):
        """Test manifest file creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "manifest.json")
            result_path = log_reproducibility_manifest(
                output_path=output_path,
                seeds=[42, 123],
                hyperparams={"lr": 0.001},
                versions={"torch": "2.0.0"}
            )
            
            assert result_path.exists()
            
            with open(result_path) as f:
                data = json.load(f)
            
            assert "timestamp" in data
            assert data["seeds"] == [42, 123]
            assert data["hyperparameters"]["lr"] == 0.001
            assert data["versions"]["torch"] == "2.0.0"
    
    def test_manifest_creates_directories(self):
        """Test that manifest creation creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "manifest.json")
            result_path = log_reproducibility_manifest(
                output_path=nested_path,
                seeds=[42],
                hyperparams={},
                versions={}
            )
            
            assert result_path.exists()
    
    def test_manifest_with_experiment_id(self):
        """Test manifest with custom experiment ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "manifest.json")
            log_reproducibility_manifest(
                output_path=output_path,
                seeds=[42],
                hyperparams={},
                versions={},
                experiment_id="custom_exp"
            )
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert data["experiment_id"] == "custom_exp"

class TestLogEvent:
    """Tests for log_event function."""
    
    def test_log_event_basic(self):
        """Test basic event logging."""
        # Just verify it doesn't raise an exception
        log_event("test_event", "Test message")
    
    def test_log_event_with_extra_data(self):
        """Test event logging with extra data."""
        log_event("test_event", "Test message", {
            "key": "value",
            "number": 42
        })
    
    def test_log_event_with_seed(self):
        """Test event logging with seed."""
        log_event("test_event", "Test message", seed=123)

class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_console_only(self):
        """Test setup with console logging only."""
        logger = setup_logging(log_level="DEBUG")
        assert len(logger.handlers) >= 1
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_with_file(self):
        """Test setup with file logging."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
            log_file = f.name
        
        try:
            logger = setup_logging(log_file=log_file)
            assert len(logger.handlers) >= 2  # Console + File
            
            # Log something
            logger.info("Test log message")
            
            # Check file has content
            with open(log_file) as f:
                content = f.read()
            
            assert "Test log message" in content
        finally:
            os.unlink(log_file)
    
    def test_setup_logging_extra_fields(self):
        """Test setup with extra fields."""
        logger = setup_logging(extra_fields=["custom_field"])
        assert len(logger.handlers) >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])