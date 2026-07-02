"""
Unit tests for code/utils.py logging and error handling infrastructure.
"""
import pytest
import logging
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.utils import (
    setup_logging,
    get_logger,
    handle_error,
    log_execution_time,
    safe_execute,
    ResourceMonitor,
    get_ram_usage_mb,
    configure_error_handling
)

class TestLogging:
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging returns a configured logger."""
        logger = setup_logging(level=logging.DEBUG)
        assert logger is not None
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0

    def test_setup_logging_file_handler(self):
        """Test that setup_logging creates a file handler when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override LOGS_DIR
            import code.utils
            original_logs_dir = code.utils.LOGS_DIR
            code.utils.LOGS_DIR = Path(tmpdir)
            
            try:
                logger = setup_logging(log_file="test.log")
                file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
                assert len(file_handlers) == 1
                assert file_handlers[0].baseFilename.endswith("test.log")
            finally:
                code.utils.LOGS_DIR = original_logs_dir

    def test_get_logger_returns_existing(self):
        """Test that get_logger returns the same logger instance."""
        logger1 = setup_logging(name="test_unique")
        logger2 = get_logger("test_unique")
        assert logger1 is logger2

    def test_logger_can_log_messages(self, caplog):
        """Test that logger can actually log messages."""
        with caplog.at_level(logging.INFO):
            logger = get_logger("test_log_msg")
            logger.info("Test message")
            assert "Test message" in caplog.text

class TestErrorHandler:
    def test_handle_error_logs_to_console(self, caplog):
        """Test that handle_error logs to the console."""
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error")
            except Exception as e:
                handle_error(e, context="Test context")
            assert "Test context" in caplog.text
            assert "ValueError" in caplog.text

    def test_handle_error_writes_to_jsonl(self):
        """Test that handle_error writes structured error to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import code.utils
            original_logs_dir = code.utils.LOGS_DIR
            code.utils.LOGS_DIR = Path(tmpdir)
            
            try:
                try:
                    raise RuntimeError("Test runtime error")
                except Exception as e:
                    handle_error(e, context="Error test")
                
                error_file = Path(tmpdir) / "errors.jsonl"
                assert error_file.exists()
                
                with open(error_file, "r") as f:
                    lines = f.readlines()
                    assert len(lines) == 1
                    error_data = json.loads(lines[0])
                    assert error_data["context"] == "Error test"
                    assert error_data["exception_type"] == "RuntimeError"
                    assert "Test runtime error" in error_data["message"]
            finally:
                code.utils.LOGS_DIR = original_logs_dir

class TestExecutionTimeDecorator:
    def test_log_execution_time_logs_duration(self, caplog):
        """Test that log_execution_time decorator logs execution duration."""
        @log_execution_time
        def slow_function():
            import time
            time.sleep(0.01)
            return "done"
        
        with caplog.at_level(logging.INFO):
            result = slow_function()
            assert result == "done"
            assert "completed in" in caplog.text
            assert "seconds" in caplog.text

    def test_log_execution_time_handles_exceptions(self, caplog):
        """Test that log_execution_time logs when function fails."""
        @log_execution_time
        def failing_function():
            raise ValueError("Failed")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()
            assert "failed after" in caplog.text

class TestSafeExecuteDecorator:
    def test_safe_execute_returns_result_on_success(self):
        """Test that safe_execute returns the function result on success."""
        @safe_execute(default="default_value")
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"

    def test_safe_execute_returns_default_on_error(self):
        """Test that safe_execute returns default value on exception."""
        @safe_execute(default="default_value")
        def fail_func():
            raise ValueError("Error")
        
        result = fail_func()
        assert result == "default_value"

    def test_safe_execute_calls_on_error_callback(self):
        """Test that safe_execute calls on_error callback."""
        callback_called = False
        
        def my_callback(exc):
            nonlocal callback_called
            callback_called = True
            assert isinstance(exc, ValueError)
        
        @safe_execute(default="default", on_error=my_callback)
        def fail_func():
            raise ValueError("Error")
        
        result = fail_func()
        assert result == "default"
        assert callback_called is True

class TestResourceMonitor:
    def test_resource_monitor_start_tracking(self):
        """Test starting resource tracking for a subject."""
        monitor = ResourceMonitor()
        monitor.start_tracking("sub-001")
        assert "sub-001" in monitor.start_times

    def test_resource_monitor_log_usage(self):
        """Test logging RAM usage for a subject."""
        monitor = ResourceMonitor()
        monitor.start_tracking("sub-002")
        monitor.log_usage("sub-002", 1024.5)
        
        assert "sub-002" in monitor.data
        assert len(monitor.data["sub-002"]["ram_samples"]) == 1
        assert monitor.data["sub-002"]["ram_samples"][0] == 1024.5

    def test_resource_monitor_finalize(self):
        """Test finalizing resource tracking."""
        monitor = ResourceMonitor()
        monitor.start_tracking("sub-003")
        monitor.log_usage("sub-003", 500.0)
        monitor.log_usage("sub-003", 600.0)
        monitor.log_usage("sub-003", 550.0)
        
        monitor.finalize("sub-003")
        
        assert monitor.data["sub-003"]["peak_ram_mb"] == 600.0
        assert monitor.data["sub-003"]["avg_ram_mb"] == pytest.approx(550.0)
        assert monitor.data["sub-003"]["sample_count"] == 3

    def test_resource_monitor_save(self):
        """Test saving resource profile to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(output_path=os.path.join(tmpdir, "resource.json"))
            monitor.start_tracking("sub-004")
            monitor.log_usage("sub-004", 100.0)
            monitor.finalize("sub-004")
            monitor.save()
            
            output_path = Path(tmpdir) / "resource.json"
            assert output_path.exists()
            
            with open(output_path, "r") as f:
                data = json.load(f)
                assert "subjects" in data
                assert "sub-004" in data["subjects"]
                assert data["subjects"]["sub-004"]["peak_ram_mb"] == 100.0

class TestGetRamUsage:
    def test_get_ram_usage_returns_number(self):
        """Test that get_ram_usage_mb returns a float."""
        usage = get_ram_usage_mb()
        assert isinstance(usage, float)
        assert usage >= 0.0

class TestConfigureErrorHandling:
    def test_configure_error_handling_sets_hook(self):
        """Test that configure_error_handling sets the global exception hook."""
        original_hook = sys.excepthook
        configure_error_handling()
        assert sys.excepthook is not original_hook
        sys.excepthook = original_hook  # Restore

if __name__ == "__main__":
    pytest.main([__file__, "-v"])