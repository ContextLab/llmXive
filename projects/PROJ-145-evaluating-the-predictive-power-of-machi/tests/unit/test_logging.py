"""Unit tests for the logging infrastructure (T004)."""
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import setup_logging, LOG_FILE, LOGS_DIR


def test_setup_logging_creates_log_file_with_timestamped_entries(tmp_path):
    # Point the log directory at a temporary location for isolation.
    import config

    original_logs_dir = config.LOGS_DIR
    original_log_file = config.LOG_FILE
    config.LOGS_DIR = tmp_path
    config.LOG_FILE = tmp_path / "app.log"
    try:
        logger = setup_logging()
        logger.info("test entry")
        for handler in logging.getLogger().handlers:
            handler.flush()
        assert config.LOG_FILE.exists()
        contents = config.LOG_FILE.read_text()
        assert "test entry" in contents
        # Timestamped entries: 'YYYY-MM-DD HH:MM:SS,mmm - name - LEVEL - msg'
        assert " - " in contents
        assert "INFO" in contents
    finally:
        config.LOGS_DIR = original_logs_dir
        config.LOG_FILE = original_log_file
        logging.getLogger().handlers.clear()


def test_setup_logging_is_idempotent():
    logger1 = setup_logging()
    n_handlers = len(logging.getLogger().handlers)
    logger2 = setup_logging()
    assert logger1 is logger2
    # No duplicate handlers after a second call.
    assert len(logging.getLogger().handlers) == n_handlers
    logging.getLogger().handlers.clear()


def test_real_log_file_exists_and_has_entries():
    # The project log file must exist after the init script has run.
    assert LOGS_DIR.exists()
    if LOG_FILE.exists():
        contents = LOG_FILE.read_text()
        assert " - " in contents  # timestamped format