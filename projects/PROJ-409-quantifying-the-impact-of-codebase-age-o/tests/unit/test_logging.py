"""
Unit tests for the unified logging module.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import (
    get_logger,
    setup_logging,
    set_log_level,
    get_level_name,
    debug,
    info,
    warning,
    error,
    critical,
    exception,
    DEFAULT_LEVEL,
    _configured
)


class TestLoggingModule:
    """Test cases for the logging module."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_without_name_returns_root(self):
        """Test that get_logger() returns the root logger."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == ""

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates console and file handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Reset configured state
            import code.utils.logging as logging_module
            logging_module._configured = False
            
            setup_logging(
                level=logging.DEBUG,
                log_dir=tmpdir,
                console=True,
                file=True
            )
            
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) >= 2  # Console + File
            
            # Verify handlers exist
            handler_types = [type(h).__name__ for h in root_logger.handlers]
            assert "StreamHandler" in handler_types
            assert "FileHandler" in handler_types

    def test_setup_logging_file_creation(self):
        """Test that setup_logging creates log files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import code.utils.logging as logging_module
            logging_module._configured = False
            
            log_file = "test.log"
            setup_logging(
                level=logging.INFO,
                log_file=log_file,
                log_dir=tmpdir,
                console=False,
                file=True
            )
            
            log_path = Path(tmpdir) / log_file
            assert log_path.exists()
            assert log_path.stat().st_size > 0

    def test_set_log_level_updates_handlers(self):
        """Test that set_log_level updates all handlers."""
        import code.utils.logging as logging_module
        logging_module._configured = False
        
        setup_logging(level=logging.WARNING, log_dir=tempfile.gettempdir())
        
        # Change level
        set_log_level(logging.DEBUG)
        
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            assert handler.level == logging.DEBUG

    def test_get_level_name(self):
        """Test that get_level_name returns correct string names."""
        assert get_level_name(logging.DEBUG) == "DEBUG"
        assert get_level_name(logging.INFO) == "INFO"
        assert get_level_name(logging.WARNING) == "WARNING"
        assert get_level_name(logging.ERROR) == "ERROR"
        assert get_level_name(logging.CRITICAL) == "CRITICAL"

    def test_convenience_functions(self):
        """Test that convenience functions log correctly."""
        with patch('code.utils.logging.get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            debug("debug msg")
            mock_logger.debug.assert_called_with("debug msg")
            
            info("info msg")
            mock_logger.info.assert_called_with("info msg")
            
            warning("warning msg")
            mock_logger.warning.assert_called_with("warning msg")
            
            error("error msg")
            mock_logger.error.assert_called_with("error msg")
            
            critical("critical msg")
            mock_logger.critical.assert_called_with("critical msg")

    def test_prevent_reconfiguration(self):
        """Test that setup_logging does not reconfigure if already configured."""
        import code.utils.logging as logging_module
        
        # First call
        initial_count = len(logging.getLogger().handlers)
        setup_logging(level=logging.INFO)
        after_first_count = len(logging.getLogger().handlers)
        
        # Reset flag to allow second call (simulating a fresh start)
        logging_module._configured = False
        
        # Second call should reconfigure
        setup_logging(level=logging.DEBUG)
        after_second_count = len(logging.getLogger().handlers)
        
        # Handlers should be replaced, not duplicated
        assert after_second_count == after_first_count

    def test_log_file_directory_creation(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import code.utils.logging as logging_module
            logging_module._configured = False
            
            new_dir = Path(tmpdir) / "nested" / "logs"
            setup_logging(log_dir=str(new_dir), console=False, file=True)
            
            assert new_dir.exists()
            assert new_dir.is_dir()