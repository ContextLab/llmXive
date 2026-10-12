import json
from pathlib import Path

def test_get_logger_creates_file():
    """
    Verify that get_logger() creates a JSON log file under data/results/
    and that a logged message is written as a valid JSON line.
    """
    from utils.logging import get_logger
    
    # Ensure the results directory exists
    log_dir = Path("data/results")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Capture existing log files to differentiate new ones
    existing_files = set(log_dir.glob("app_*.log"))
    
    logger = get_logger("test_logger")
    logger.info("test message")
    
    # Find newly created log files
    new_files = [p for p in log_dir.glob("app_*.log") if p not in existing_files]
    assert new_files, "No new log file was created by get_logger"
    
    # Read the last line of the newest log file
    newest_log = max(new_files, key=lambda p: p.stat().st_mtime)
    with newest_log.open("r") as f:
        lines = f.readlines()
        assert lines, "Log file is empty"
        last_line = lines[-1].strip()
    
    # The line should be valid JSON and contain our message
    parsed = json.loads(last_line)
    assert parsed["message"] == "test message"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"