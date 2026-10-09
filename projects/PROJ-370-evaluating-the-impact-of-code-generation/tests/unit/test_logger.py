import json
import os
from pathlib import Path

import pytest

from src.utils.logger import get_logger


def test_logger_writes_valid_json(tmp_path):
    """
    The logger should emit one JSON object per line containing the required fields.
    """
    # Redirect the logs directory to a temporary location.
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        logger_name = "unit_test_logger"
        logger = get_logger(logger_name)

        # Emit a log record.
        logger.info("Test message", extra={"custom_field": 42})

        # Verify the file exists.
        log_file = Path("logs") / f"{logger_name}.log"
        assert log_file.is_file(), "Log file was not created"

        # Read the single line and validate JSON structure.
        with log_file.open("r", encoding="utf-8") as f:
            line = f.readline().strip()
            assert line, "Log file is empty"

            payload = json.loads(line)

        # Required keys.
        for key in ("timestamp", "level", "logger", "message"):
            assert key in payload, f"Missing key {key} in log payload"

        assert payload["logger"] == logger_name
        assert payload["level"] == "INFO"
        assert payload["message"] == "Test message"
        assert payload["custom_field"] == 42

    finally:
        os.chdir(original_cwd)
