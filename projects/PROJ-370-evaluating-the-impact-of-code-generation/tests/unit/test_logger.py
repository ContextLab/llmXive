import json
import os
from pathlib import Path
import pytest
from src.utils.logger import get_logger

def test_logger_writes_valid_json(tmp_path, monkeypatch):
    """
    The logger should emit one JSON object per line containing the required fields.
    """
    # Mock Path to ensure logs are written to tmp_path
    def mock_path_mkdir(self, *args, **kwargs):
        return None
    
    # We patch the Path object inside logger.py to use tmp_path for the logs directory
    # To keep it simple, we'll just change the working directory for this test
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        logger_name = "unit_test_logger"
        logger = get_logger(logger_name)

        # Emit a log record with extra fields
        logger.info("Test message", extra={"custom_field": 42, "metric": 0.95})

        # Verify the file exists
        log_file = Path("logs") / f"{logger_name}.log"
        assert log_file.is_file(), "Log file was not created"

        # Read the line and validate JSON structure
        with log_file.open("r", encoding="utf-8") as f:
            line = f.readline().strip()
            assert line, "Log file is empty"
            payload = json.loads(line)

        # Required keys
        for key in ("timestamp", "level", "logger", "message"):
            assert key in payload, f"Missing key {key} in log payload"

        assert payload["logger"] == logger_name
        assert payload["level"] == "INFO"
        assert payload["message"] == "Test message"
        assert payload["custom_field"] == 42
        assert payload["metric"] == 0.95

    finally:
        os.chdir(original_cwd)