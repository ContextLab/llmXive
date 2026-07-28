"""
Unit tests for the configuration module (T010).

Tests cover:
- Constant values
- Logging format compliance
- File rotation setup
- Directory creation
"""
import os
import pytest
import logging
import re
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.lib import config


class TestConfigDefaults:
    """Test that default constants are set correctly."""
    
    def test_seed_value(self):
        assert config.SEED == 42
        
    def test_grid_resolution(self):
        assert config.GRID_RES == 0.5
        
    def test_sample_size(self):
        assert config.SAMPLE_SIZE == 10000
        
    def test_permutations(self):
        assert config.PERMUTATIONS == 10000


class TestConfigEnvironmentVariables:
    """Test environment variable handling (if extended in future)."""
    
    def test_root_dir_exists(self):
        assert isinstance(config.ROOT_DIR, Path)
        assert config.ROOT_DIR.exists()
        
    def test_data_dirs_created(self):
        """Verify that data directories are created on import."""
        assert config.DATA_DIR.exists()
        assert config.RAW_DATA_DIR.exists()
        assert config.INTERIM_DATA_DIR.exists()
        assert config.PROCESSED_DATA_DIR.exists()
        
    def test_logs_dir_created(self):
        assert config.LOGS_DIR.exists()


class TestConfigMethods:
    """Test configuration utility methods."""
    
    def test_verify_logging_config(self):
        """Test that logging verification returns True for valid config."""
        # Reset logger handlers to ensure clean state
        config.logger.handlers = []
        config.logger = config.setup_logging()
        
        result = config.verify_logging_config()
        assert result is True
        
    def test_log_format_compliance(self):
        """Verify log entries match the expected format."""
        config.logger.handlers = []
        config.logger = config.setup_logging()
        
        # Clear log file
        if config.LOG_FILE.exists():
            config.LOG_FILE.unlink()
            
        config.logger.info("Test Message")
        
        with open(config.LOG_FILE, 'r') as f:
            line = f.readline().strip()
        
        # Pattern: YYYY-MM-DD HH:MM:SS,mmm - name - LEVEL - message
        pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \w+ - \w+ - .+'
        assert re.match(pattern, line) is not None
        
    def test_log_rotation_setup(self):
        """Verify that rotating file handler is configured."""
        config.logger.handlers = []
        config.logger = config.setup_logging()
        
        has_rotating_handler = any(
            isinstance(h, logging.handlers.RotatingFileHandler)
            for h in config.logger.handlers
        )
        assert has_rotating_handler


class TestGlobalConfig:
    """Test global logger instance."""
    
    def test_logger_type(self):
        assert isinstance(config.logger, logging.Logger)
        
    def test_logger_level(self):
        assert config.logger.level == logging.INFO


class TestConfigEdgeCases:
    """Test edge cases and error handling."""
    
    def test_directory_creation_failure_handling(self):
        """Test that setup_logging handles file creation errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Point log to a read-only location (simulate failure)
            with patch.object(config, 'LOG_FILE', Path(tmpdir) / "readonly" / "test.log"):
                # This should not crash, just warn
                logger = config.setup_logging()
                assert isinstance(logger, logging.Logger)


class TestIntegrationWithPipeline:
    """Test that config integrates with other modules."""
    
    def test_constants_used_in_pipeline(self):
        """Verify constants are accessible to pipeline modules."""
        # Simulate what a pipeline module would do
        seed = config.SEED
        grid_res = config.GRID_RES
        
        assert seed == 42
        assert grid_res == 0.5


class TestTaskRequirements:
    """Specific requirements from T010 task description."""
    
    def test_log_format_string(self):
        """Verify LOG_FORMAT matches task specification."""
        expected = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.LOG_FORMAT == expected
        
    def test_rotation_policy(self):
        """Verify rotation policy: max 10MB, 5 backup files."""
        assert config.MAX_BYTES == 10 * 1024 * 1024
        assert config.BACKUP_COUNT == 5
        
    def test_verification_function_exists(self):
        """Verify verify_logging_config function exists and is callable."""
        assert callable(config.verify_logging_config)
        
    def test_verification_returns_boolean(self):
        """Verify verification function returns a boolean."""
        result = config.verify_logging_config()
        assert isinstance(result, bool)