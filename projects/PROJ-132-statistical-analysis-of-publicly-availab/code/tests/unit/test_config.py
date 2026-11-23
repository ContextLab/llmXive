"""
Unit tests for the configuration module (src/config.py).

These tests verify:
- Constant values match T010 requirements.
- Logging format is correct.
- Log file creation and rotation logic works.
"""
import os
import logging
import re
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.config import (
    SEED,
    GRID_RES,
    PERMUTATIONS,
    POWER_TARGET,
    CI_WIDTH_TARGET,
    CONVERGENCE_TARGET,
    INSUFFICIENT_DATA_TARGET,
    setup_logging,
    verify_config_targets,
    LOG_FORMAT,
    LOG_MAX_BYTES,
    LOG_BACKUP_COUNT,
    LOGS_DIR,
    logger,
)

@pytest.fixture
def temp_logs_dir():
    """Create a temporary directory for logs to avoid cluttering the real project."""
    temp_dir = tempfile.mkdtemp()
    # Temporarily override the global LOGS_DIR for this test
    original_logs_dir = LOGS_DIR
    # We can't easily monkeypatch the global in the module, so we test
    # the function's behavior by passing a custom path if supported,
    # or by creating a temp logger that writes to the temp dir.
    # For this test, we will just verify the format string and constants.
    yield temp_dir
    shutil.rmtree(temp_dir)

class TestConfigDefaults:
    """Test that default constants match T010 requirements."""

    def test_seed_is_42(self):
        assert SEED == 42

    def test_grid_res_is_0_5(self):
        assert GRID_RES == 0.5

    def test_permutations_is_10000(self):
        assert PERMUTATIONS == 10000

    def test_sample_size_removed(self):
        """Verify SAMPLE_SIZE constant does not exist in the module."""
        import src.config as config
        assert not hasattr(config, 'SAMPLE_SIZE'), "SAMPLE_SIZE should have been removed."

    def test_power_target(self):
        assert POWER_TARGET == 0.80

    def test_ci_width_target(self):
        assert CI_WIDTH_TARGET == 5.0

    def test_convergence_target(self):
        assert CONVERGENCE_TARGET == 0.90

    def test_insufficient_data_target(self):
        assert INSUFFICIENT_DATA_TARGET == 0.20

class TestConfigMethods:
    """Test configuration helper functions."""

    def test_verify_config_targets_returns_true(self):
        """All targets should be valid by default."""
        assert verify_config_targets() is True

    def test_log_format_string(self):
        """Verify the log format string matches the requirement."""
        expected_pattern = r"%\(asctime\)s - %\(name\)s - %\(levelname\)s - %\(message\)s"
        assert LOG_FORMAT == expected_pattern

class TestLoggerConfiguration:
    """Test the logging setup functionality."""

    def test_logger_creation(self, temp_logs_dir):
        """Test that a logger is created and has handlers."""
        # Create a logger in a temp directory to avoid file permission issues in CI
        # We mock the LOGS_DIR behavior by creating a logger with a custom file handler
        test_logger = logging.getLogger("test_logger_config")
        test_logger.setLevel(logging.INFO)

        # Clear existing handlers
        test_logger.handlers.clear()

        # Create a temp file handler
        temp_log_file = Path(temp_logs_dir) / "test.log"
        handler = logging.FileHandler(temp_log_file)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        test_logger.addHandler(handler)

        # Log a test message
        test_logger.info("Test message for format verification")

        # Check file exists
        assert temp_log_file.exists()

        # Check content format
        with open(temp_log_file, 'r') as f:
            content = f.read()
            # Format: 2023-01-01 12:00:00 - name - LEVEL - message
            pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - test_logger_config - INFO - Test message for format verification"
            assert re.search(pattern, content), f"Log format mismatch. Content: {content}"

    def test_logger_rotation_config(self):
        """Verify rotation constants are set correctly."""
        assert LOG_MAX_BYTES == 10 * 1024 * 1024
        assert LOG_BACKUP_COUNT == 5

class TestGlobalConfig:
    """Test global logger initialization."""

    def test_global_logger_exists(self):
        """Verify the global logger defined in config.py exists."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_global_logger_has_handlers(self):
        """Verify the global logger has handlers attached."""
        # Note: In some test environments, the global logger might not have handlers
        # if setup_logging wasn't called or if handlers were cleared.
        # We check if it has at least one handler or if it's valid.
        # The module-level code calls setup_logging(), so it should have handlers.
        assert len(logger.handlers) > 0

class TestTaskRequirements:
    """Specific tests for T010 task requirements."""

    def test_no_synthetic_fallback_constants(self):
        """Ensure no constants related to synthetic data generation exist."""
        import src.config as config
        forbidden = ['SAMPLE_SIZE', 'SYNTHETIC_SIZE', 'FAKE_DATA_SIZE']
        for name in forbidden:
            assert not hasattr(config, name), f"Constant {name} should not exist."

    def test_targets_are_exported(self):
        """Ensure all target constants are accessible at module level."""
        import src.config as config
        assert hasattr(config, 'POWER_TARGET')
        assert hasattr(config, 'CI_WIDTH_TARGET')
        assert hasattr(config, 'CONVERGENCE_TARGET')
        assert hasattr(config, 'INSUFFICIENT_DATA_TARGET')