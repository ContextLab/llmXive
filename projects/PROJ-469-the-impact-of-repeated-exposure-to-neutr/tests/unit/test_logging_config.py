import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the config module to avoid dependency issues in unit tests
class MockConfig:
    @staticmethod
    def ensure_dirs():
        pass

# Inject mock before importing logging_config
sys.modules['config'] = MockConfig

from logging_config import (
    ColorFormatter,
    setup_logging,
    get_logger,
    log_exception,
    handle_critical_error
)

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create necessary subdirectories
    Path("logs").mkdir()
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

class TestColorFormatter:
    def test_format_adds_colors(self):
        formatter = ColorFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Check that ANSI codes are present
        assert '\033[32m' in formatted  # Green for INFO
        assert '\033[0m' in formatted   # Reset code

    def test_format_handles_unknown_level(self):
        formatter = ColorFormatter('%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name="test",
            level=999,  # Unknown level
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        # Should still format without crashing
        assert "Test message" in formatted

class TestSetupLogging:
    def test_setup_creates_handlers(self, temp_log_dir):
        logger = setup_logging(log_level="DEBUG", log_file="test.log")
        
        assert len(logger.handlers) == 2  # File and Console
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        
        # Check file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        assert "test.log" in file_handlers[0].baseFilename

    def test_setup_sets_levels(self, temp_log_dir):
        logger = setup_logging(log_level="WARNING", log_file="test.log")
        
        console_handler = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)][0]
        assert console_handler.level == logging.WARNING

    def test_setup_creates_log_file(self, temp_log_dir):
        logger = setup_logging(log_file="test.log")
        logger.info("Test message")
        
        log_path = Path("logs") / "test.log"
        assert log_path.exists()

class TestGetLogger:
    def test_get_logger_returns_named_logger(self, temp_log_dir):
        setup_logging()
        logger = get_logger("my_module")
        
        assert logger.name == "my_module"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_reuses_root(self, temp_log_dir):
        setup_logging()
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Both should share the same handlers from root
        assert len(logger1.root.handlers) == len(logger2.root.handlers)

class TestLogException:
    def test_log_exception_logs_traceback(self, temp_log_dir):
        setup_logging(log_file="test.log")
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            log_exception(e, "Test context")
        
        log_path = Path("logs") / "test.log"
        content = log_path.read_text()
        
        assert "Test context" in content
        assert "ValueError" in content
        assert "Traceback" in content

class TestHandleCriticalError:
    def test_handle_critical_error_exits(self, temp_log_dir, caplog):
        setup_logging(log_file="test.log")
        
        with pytest.raises(SystemExit) as exc_info:
            handle_critical_error(ValueError("Fatal error"), exit_code=42)
        
        assert exc_info.value.code == 42
        
        log_path = Path("logs") / "test.log"
        content = log_path.read_text()
        
        assert "FATAL ERROR" in content
        assert "Fatal error" in content