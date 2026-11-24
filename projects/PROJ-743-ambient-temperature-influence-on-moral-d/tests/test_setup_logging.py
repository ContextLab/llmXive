"""
Unit tests for the logging utilities introduced in T001.
"""
import logging
from pathlib import Path

from setup_logging import get_data_quality_logger, get_exclusion_logger


def test_data_quality_logger_writes_to_file(tmp_path: Path):
    # Redirect the logger to a temporary file
    log_file = tmp_path / "data_quality.log"
    logger = get_data_quality_logger()
    
    # Ensure the logger has a file handler pointing to our temp file
    # Remove existing file handlers to avoid duplication
    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            logger.removeHandler(h)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    test_msg = "test message for data quality logger"
    logger.info(test_msg)
    file_handler.flush()

    content = log_file.read_text(encoding="utf-8")
    assert test_msg in content


def test_exclusion_logger_is_configured():
    logger = get_exclusion_logger()
    # Should have at least one handler (the console handler)
    assert logger.handlers
    # Ensure the logger level is INFO (as set in the helper)
    assert logger.level == logging.INFO