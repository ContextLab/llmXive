import json
from pathlib import Path

def test_setup_logger_creates_file():
    # Import the module which should run setup_logger on import
    import importlib
    logging_mod = importlib.import_module("code.utils.logging")
    
    # Ensure the logger function can be called again without error
    logger = logging_mod.setup_logger()
    assert logger.name == "app"

    # Verify that the log file exists
    log_file = Path("data/logs/app.log")
    assert log_file.exists(), "app.log was not created"

    # Verify that the file contains at least one JSON line
    with open(log_file, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        assert first_line, "app.log is empty"
        # Attempt to parse JSON
        parsed = json.loads(first_line)
        # Check required keys
        for key in ("timestamp", "level", "logger", "message"):
            assert key in parsed, f"Missing key {key} in log entry"