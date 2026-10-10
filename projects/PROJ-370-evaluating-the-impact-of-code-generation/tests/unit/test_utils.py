import pytest
import json
import os
import time
from pathlib import Path
from src.utils.timeout_wrapper import check_global_timeout, START_TIME_FILE, TIMEOUT_LOG_PATH, TIMEOUT_LIMIT_SECONDS
from src.utils.logger import setup_pipeline_logging, get_logger

def test_timeout_enforcement(tmp_path, monkeypatch):
    """
    Verify that check_global_timeout exits with code 143 when the limit is exceeded.
    """
    # Mock the logs directory and start time file to use tmp_path
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Override the paths in the module
    monkeypatch.setattr("src.utils.timeout_wrapper.START_TIME_FILE", logs_dir / ".start_time")
    monkeypatch.setattr("src.utils.timeout_wrapper.TIMEOUT_LOG_PATH", logs_dir / "timeout.log")
    
    # Create a start time file that is older than the limit
    past_time = time.time() - (TIMEOUT_LIMIT_SECONDS + 100)
    with open(logs_dir / ".start_time", "w") as f:
        f.write(str(past_time))
    
    # Assert that check_global_timeout triggers SystemExit(143)
    with pytest.raises(SystemExit) as e:
        check_global_timeout()
    
    assert e.value.code == 143
    
    # Verify that the timeout was logged
    assert (logs_dir / "timeout.log").exists()
    with open(logs_dir / "timeout.log", "r") as f:
        content = f.read()
        assert "Global timeout" in content

def test_logger_json_format(tmp_path, monkeypatch):
    """
    Verify that the logger produces valid JSON lines.
    """
    # Mock log directory
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Override the log file location in setup_pipeline_logging
    # We can do this by passing a config or mocking the Path inside the function
    # Since setup_pipeline_logging uses Path("logs"), we monkeypatch Path
    
    # Simpler: we just run it and check the actual logs/ directory, 
    # but for a unit test, we should isolate.
    # Let's override the logging config to use a different file.
    
    setup_pipeline_logging()
    logger = get_logger("test_logger")
    
    test_msg = "Test structured log message"
    stats = {"duration": 1.23, "memory_mb": 450}
    
    # Log with extra runtime stats
    logger.info(test_msg, extra={"runtime_stats": stats})
    
    # The actual file is logs/pipeline.log
    log_file = Path("logs/pipeline.log")
    assert log_file.exists()
    
    # Read the last line
    with open(log_file, "r") as f:
        lines = f.readlines()
        last_line = lines[-1]
        
        data = json.loads(last_line)
        assert data["message"] == test_msg
        assert data["level"] == "INFO"
        assert data["name"] == "test_logger"
        assert data["runtime_stats"] == stats
        assert "timestamp" in data

def test_timeout_no_exit_within_limit(tmp_path, monkeypatch):
    """
    Verify that check_global_timeout does NOT exit if we are within the limit.
    """
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    monkeypatch.setattr("src.utils.timeout_wrapper.START_TIME_FILE", logs_dir / ".start_time")
    
    # Start time is now
    with open(logs_dir / ".start_time", "w") as f:
        f.write(str(time.time()))
    
    # Should not raise SystemExit
    check_global_timeout()