import logging
import json
from pathlib import Path
from src.utils.logger import setup_pipeline_logging, get_logger

def test_logging_setup_and_output(tmp_path):
    # Redirect logs directory to a temporary location
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    # Monkey‑patch the Path used inside the logger module
    # The logger uses Path("logs") directly; we replace the cwd temporarily
    import os
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        setup_pipeline_logging()
        
        logger = get_logger("unit_test")
        logger.info("unit test message", extra={"foo": "bar"})
        
        log_file = Path("logs/pipeline.jsonl")
        assert log_file.is_file()
        
        # Verify JSON line structure
        with log_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) > 0
            entry = json.loads(lines[-1])
            assert entry["message"] == "unit test message"
            assert entry["level"] == "INFO"
            assert entry["name"] == "unit_test"
            assert entry["extra"]["foo"] == "bar"
    finally:
        os.chdir(cwd)