import logging
import builtins

import pytest

from utils import setup_logging


def test_setup_logging_various_signatures():
    # Default call
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO

    # Positional level only
    logger = setup_logging("DEBUG")
    assert logger.level == logging.DEBUG

    # Name then level
    logger = setup_logging("my_logger", "WARNING")
    assert logger.name == "my_logger"
    assert logger.level == logging.WARNING

    # Keyword name only
    logger = setup_logging(name="kw_logger")
    assert logger.name == "kw_logger"
    assert logger.level == logging.INFO

    # Keyword level only
    logger = setup_logging(log_level="ERROR")
    assert logger.level == logging.ERROR

    # Mixed positional/keyword
    logger = setup_logging("mixed_logger", log_level="CRITICAL")
    assert logger.name == "mixed_logger"
    assert logger.level == logging.CRITICAL


def test_setup_logging_idempotent_handler():
    """
    Ensure that repeated calls with the same logger name do not add duplicate handlers.
    """
    logger1 = setup_logging("dup_logger", "INFO")
    handler_count_before = len(logger1.handlers)
    logger2 = setup_logging("dup_logger", "INFO")
    handler_count_after = len(logger2.handlers)
    assert handler_count_before == handler_count_after