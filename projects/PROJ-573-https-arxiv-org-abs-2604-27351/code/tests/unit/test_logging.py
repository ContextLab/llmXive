import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import yaml

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import (
    setup_logger,
    get_logger,
    log_environment,
    log_random_seed,
    log_model_versions,
    log_configuration,
    _loggers
)

class TestLoggingUtils:
    """Tests for the logging utility functions."""

    def setup_method(self):
        """Setup before each test."""
        # Clear the logger cache to ensure clean state
        _loggers.clear()
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def teardown_method(self):
        """Teardown after each test."""
        # Clean up temp files
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_setup_logger_creates_logger(self):
        """Test that setup_logger creates and returns a logger."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0

    def test_setup_logger_with_file(self):
        """Test that setup_logger creates a file handler when log_file is provided."""
        logger = setup_logger("test_file_logger", log_file=self.log_file)
        assert isinstance(logger, logging.Logger)
        
        # Check if file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_setup_logger_idempotent(self):
        """Test that calling setup_logger multiple times returns the same logger."""
        logger1 = setup_logger("idempotent_logger")
        logger2 = setup_logger("idempotent_logger")
        assert logger1 is logger2

    def test_get_logger_returns_existing(self):
        """Test that get_logger returns an existing logger."""
        # First setup
        logger1 = setup_logger("get_test_logger")
        # Then get
        logger2 = get_logger("get_test_logger")
        assert logger1 is logger2

    def test_get_logger_creates_default(self):
        """Test that get_logger creates a default logger if not found."""
        logger = get_logger("non_existent_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "non_existent_logger"

    def test_log_environment(self, caplog):
        """Test that log_environment logs system information."""
        with caplog.at_level(logging.INFO):
            log_environment()
        
        # Check that specific keywords are in the logs
        log_text = "\n".join(caplog.messages)
        assert "ENVIRONMENT DETAILS" in log_text
        assert "Python Version" in log_text
        assert "Operating System" in log_text

    def test_log_random_seed(self, caplog):
        """Test that log_random_seed logs the seed value."""
        test_seed = 12345
        with caplog.at_level(logging.INFO):
            log_random_seed(test_seed)
        
        log_text = "\n".join(caplog.messages)
        assert f"RANDOM SEED: {test_seed}" in log_text

    def test_log_model_versions(self, caplog):
        """Test that log_model_versions logs model information correctly."""
        models = [
            {
                'model_id': 'test-model-1',
                'model_type': 'Transformer',
                'version': '1.0.0',
                'source': 'huggingface'
            }
        ]
        
        with caplog.at_level(logging.INFO):
            log_model_versions(models)
        
        log_text = "\n".join(caplog.messages)
        assert "MODEL VERSIONS" in log_text
        assert "test-model-1" in log_text
        assert "Transformer" in log_text
        assert "1.0.0" in log_text

    def test_log_model_versions_empty(self, caplog):
        """Test that log_model_versions handles empty list gracefully."""
        with caplog.at_level(logging.WARNING):
            log_model_versions([])
        
        log_text = "\n".join(caplog.messages)
        assert "No model versions provided to log" in log_text

    def test_log_configuration(self, caplog):
        """Test that log_configuration logs dictionary correctly."""
        config = {
            'key1': 'value1',
            'key2': {
                'nested_key': 'nested_value'
            },
            'list_key': ['item1', 'item2']
        }
        
        with caplog.at_level(logging.INFO):
            log_configuration(config, "Test Config")
        
        log_text = "\n".join(caplog.messages)
        assert "TEST CONFIG" in log_text
        assert "key1: value1" in log_text
        assert "nested_key: nested_value" in log_text
        assert "item1" in log_text

    def test_log_configuration_empty(self, caplog):
        """Test that log_configuration handles empty dict."""
        with caplog.at_level(logging.INFO):
            log_configuration({}, "Empty Config")
        
        log_text = "\n".join(caplog.messages)
        assert "EMPTY CONFIG" in log_text

    def test_logger_level_setting(self):
        """Test that logger level is set correctly."""
        logger = setup_logger("level_test", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

        logger2 = setup_logger("level_test_info", level=logging.INFO)
        assert logger2.level == logging.INFO

    def test_rotating_file_handler(self):
        """Test that RotatingFileHandler is used when log_file is provided."""
        logger = setup_logger("rotating_test", log_file=self.log_file, max_bytes=1024, backup_count=3)
        
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        assert len(file_handlers) == 1
        
        handler = file_handlers[0]
        assert handler.maxBytes == 1024
        assert handler.backupCount == 3

    def test_log_environment_masks_sensitive_vars(self, caplog):
        """Test that log_environment masks sensitive environment variables."""
        # Set a fake sensitive variable
        os.environ['TEST_SECRET_KEY'] = 'super_secret_123'
        
        with caplog.at_level(logging.INFO):
            log_environment()
        
        log_text = "\n".join(caplog.messages)
        assert "***MASKED***" in log_text
        assert "super_secret_123" not in log_text

        # Clean up
        del os.environ['TEST_SECRET_KEY']