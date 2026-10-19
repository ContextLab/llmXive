# Placeholder test file – the real logger tests are part of the broader suite.
# This file exists to ensure the test discovery mechanism works.
import logging
import sys

from orchestrator.logger import get_logger

def test_logger_basic():
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    # Ensure the logger has at least one handler (the default StreamHandler)
    assert len(logger.handlers) > 0
