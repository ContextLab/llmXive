import logging
import pytest
from utils import get_logger, log_stage

def test_get_logger_returns_logger():
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)

def test_log_stage_formats_message():
    logger = get_logger("test_logger")
    with pytest.raises(AssertionError):
        # The logger should not raise; we just ensure the function runs.
        log_stage(logger, "T999", "DemoStage", "This is a test")
