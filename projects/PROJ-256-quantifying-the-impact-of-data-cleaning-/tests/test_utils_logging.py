"""
Basic sanity tests for the updated ``utils.setup_logging`` implementation.
These tests ensure that the function can be called with the various signatures
observed throughout the repository without raising exceptions and that it
returns a ``logging.Logger`` instance.
"""
import logging

from utils import setup_logging


def test_setup_logging_default():
    logger = setup_logging()
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.WARNING


def test_setup_logging_log_level_positional():
    logger = setup_logging("INFO")
    assert logger.level == logging.INFO


def test_setup_logging_name_and_level():
    logger = setup_logging("my_logger", "DEBUG")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "my_logger"
    assert logger.level == logging.DEBUG


def test_setup_logging_kwargs():
    logger = setup_logging(name="custom_logger", log_level="ERROR")
    assert logger.name == "custom_logger"
    assert logger.level == logging.ERROR
