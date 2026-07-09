"""
Unit tests for logging configuration and memory hooks.
"""
import pytest
import logging
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from logging_config import (
    get_logger, 
    initialize_logging, 
    set_log_level, 
    log_memory_warning,
    _check_memory_and_log,
    _memory_hook_enabled,
    MEMORY_WARNING_THRESHOLD_GB,
    MEMORY_LIMIT_GB
)
from memory_monitor import get_current_ram_gb

class TestLoggingConfig:
    """Tests for the logging configuration module."""

    def setup_method(self):
        """Reset logger state before each test."""
        # Reset the global logger instance
        import logging_config
        logging_config._logger = None
        logging_config._memory_hook_enabled = False
        
        # Remove handlers from root logger to prevent interference
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    def test_initialize_logging_creates_logger(self):
        """Test that initialize_logging creates a logger instance."""
        initialize_logging(memory_hooks=False)
        logger = get_logger()
        assert logger is not None
        assert logger.name == "llmXive"
        assert len(logger.handlers) > 0

    def test_initialize_logging_with_memory_hooks(self):
        """Test that memory hooks are enabled when requested."""
        initialize_logging(memory_hooks=True)
        import logging_config
        assert logging_config._memory_hook_enabled is True

    def test_initialize_logging_without_memory_hooks(self):
        """Test that memory hooks are disabled when not requested."""
        initialize_logging(memory_hooks=False)
        import logging_config
        assert logging_config._memory_hook_enabled is False

    def test_set_log_level(self):
        """Test that set_log_level updates handler levels."""
        initialize_logging(memory_hooks=False)
        set_log_level(logging.DEBUG)
        logger = get_logger()
        for handler in logger.handlers:
            assert handler.level == logging.DEBUG

    def test_log_memory_warning_calls_check(self):
        """Test that log_memory_warning triggers the memory check."""
        initialize_logging(memory_hooks=True)
        
        with patch('logging_config._check_memory_and_log') as mock_check:
            log_memory_warning()
            mock_check.assert_called_once()

    def test_memory_warning_threshold_constant(self):
        """Test that the memory warning threshold is set correctly."""
        assert MEMORY_WARNING_THRESHOLD_GB == 5.1

    def test_memory_limit_constant(self):
        """Test that the memory limit is set correctly."""
        assert MEMORY_LIMIT_GB == 6.0

    def test_check_memory_and_log_when_disabled(self):
        """Test that memory check does nothing when hooks are disabled."""
        import logging_config
        logging_config._memory_hook_enabled = False
        
        with patch('logging_config.get_current_ram_gb') as mock_ram:
            _check_memory_and_log()
            mock_ram.assert_not_called()

    def test_check_memory_and_log_emits_warning(self):
        """Test that a warning is logged when RAM approaches limit."""
        import logging_config
        logging_config._memory_hook_enabled = True
        
        # Mock RAM usage above warning threshold
        with patch('logging_config.get_current_ram_gb', return_value=5.5):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                _check_memory_and_log()
                
                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args[0][0]
                assert "Time Limit Warning" in call_args
                assert "5.50" in call_args

    def test_check_memory_and_log_emits_critical(self):
        """Test that a critical log is emitted when RAM exceeds limit."""
        import logging_config
        logging_config._memory_hook_enabled = True
        
        # Mock RAM usage above limit
        with patch('logging_config.get_current_ram_gb', return_value=6.5):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                _check_memory_and_log()
                
                # Verify critical was logged
                mock_logger.critical.assert_called_once()
                call_args = mock_logger.critical.call_args[0][0]
                assert "CRITICAL" in call_args
                assert "Memory limit exceeded" in call_args

    def test_check_memory_and_log_handles_import_error(self):
        """Test that memory check handles ImportError gracefully."""
        import logging_config
        logging_config._memory_hook_enabled = True
        
        with patch.dict('sys.modules', {'memory_monitor': None}):
            # Should not raise an exception
            _check_memory_and_log()
            
    def test_check_memory_and_log_handles_general_exception(self):
        """Test that memory check handles general exceptions gracefully."""
        import logging_config
        logging_config._memory_hook_enabled = True
        
        with patch('logging_config.get_current_ram_gb', side_effect=Exception("Test error")):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                # Should not raise an exception
                _check_memory_and_log()
                
                # Verify debug log was written
                mock_logger.debug.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
