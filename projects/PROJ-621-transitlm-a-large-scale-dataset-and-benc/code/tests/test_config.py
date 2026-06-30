"""
Tests for the configuration and logging infrastructure.
"""

import logging
import os
import tempfile
import random
from pathlib import Path
import pytest

from src.lib.config import (
    set_seed,
    get_seed,
    get_logger,
    configure_logging,
    init_project_config,
    DEFAULT_SEED
)


class TestSeedConfiguration:
    def test_set_seed_updates_global_seed(self):
        """Test that set_seed updates the global seed variable."""
        test_seed = 12345
        set_seed(test_seed)
        assert get_seed() == test_seed

    def test_set_seed_defaults_to_42(self):
        """Test that get_seed returns 42 if no seed has been set yet."""
        # Reset seed by importing fresh or setting to default
        set_seed(DEFAULT_SEED)
        assert get_seed() == DEFAULT_SEED

    def test_set_seed_affects_random(self):
        """Test that set_seed affects Python's random module."""
        set_seed(42)
        val1 = random.random()

        set_seed(42)
        val2 = random.random()

        assert val1 == val2

    def test_set_seed_affects_numpy(self):
        """Test that set_seed affects numpy's random state."""
        import numpy as np
        set_seed(42)
        arr1 = np.random.rand(5)

        set_seed(42)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2)


class TestLoggerConfiguration:
    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = get_logger("test_unique_name_123")
        logger2 = get_logger("test_unique_name_123")
        assert logger1 is logger2

    def test_get_logger_sets_level(self):
        """Test that get_logger respects the log_level argument."""
        logger = get_logger("test_level_456", log_level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_get_logger_creates_file_handler(self):
        """Test that get_logger creates a file handler when log_file is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = get_logger("test_file_789", log_file=log_file)

            # Check that a FileHandler exists
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0

            # Log something and verify file exists
            logger.info("Test message")
            assert log_file.exists()

    def test_configure_logging_sets_root_handlers(self):
        """Test that configure_logging sets up root logger handlers."""
        # Clear root handlers first
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        configure_logging(level="WARNING")

        # Check that console handler exists
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_configure_logging_file_output(self):
        """Test that configure_logging writes to a file if log_dir is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "config_test.log"
            configure_logging(level="INFO", log_dir=tmpdir, log_file_name="config_test.log")

            logger = logging.getLogger("config_test")
            logger.info("Config test message")

            # Verify file was created and contains message
            assert log_path.exists()
            content = log_path.read_text()
            assert "Config test message" in content


class TestInitProjectConfig:
    def test_init_project_config_sets_seed_and_logger(self):
        """Test that init_project_config initializes both seed and logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = init_project_config(
                seed=999,
                log_level="DEBUG",
                log_dir=tmpdir
            )

            assert get_seed() == 999
            assert logger.level == logging.DEBUG

            # Check for log file
            log_file = Path(tmpdir) / "transitlm.log"
            assert log_file.exists()

    def test_init_project_config_default_values(self):
        """Test that init_project_config uses defaults when no args provided."""
        logger = init_project_config()
        assert get_seed() == DEFAULT_SEED
        assert logger.level == logging.INFO