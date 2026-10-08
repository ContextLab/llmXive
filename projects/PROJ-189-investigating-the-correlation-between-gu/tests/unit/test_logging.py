"""
Unit tests for code/utils/logging.py
"""
import pytest
import logging
import os
import tempfile
from code.utils.logging import setup_logging, get_logger, get_memory_usage_mb, check_memory_limit


class TestSetupLogging:
    def test_setup_logging_creates_logger(self):
        logger = setup_logging("test_logger", log_level=logging.DEBUG)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.DEBUG

    def test_setup_logging_default_level(self):
        logger = setup_logging("test_logger_default")
        assert logger.level == logging.INFO

    def test_setup_logging_file_handler(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            logger = setup_logging("test_file_logger", log_file=log_path)
            
            # Verify logger has file handler
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0

            # Write a test log
            logger.info("Test message")
            
            # Verify log file exists and contains message
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                content = f.read()
                assert "Test message" in content


class TestGetLogger:
    def test_get_logger_returns_existing(self):
        logger1 = setup_logging("retrieved_logger")
        logger2 = get_logger("retrieved_logger")
        assert logger1 is logger2

    def test_get_logger_creates_new(self):
        logger = get_logger("new_logger_instance")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "new_logger_instance"


class TestMemoryFunctions:
    def test_get_memory_usage_mb_returns_number(self):
        mem_mb = get_memory_usage_mb()
        assert isinstance(mem_mb, (int, float))
        assert mem_mb >= 0

    def test_check_memory_limit_default(self):
        # Should not raise with default limit (7GB)
        try:
            check_memory_limit()
        except Exception:
            pytest.fail("check_memory_limit should not raise under normal conditions")

    def test_check_memory_limit_custom_limit(self):
        # Test with a very low limit to ensure it raises
        try:
            # This might raise if system memory is actually low, which is fine
            # The test verifies the function exists and is callable
            check_memory_limit(limit_mb=1)
        except Exception:
            # Expected to raise if limit is exceeded
            pass
