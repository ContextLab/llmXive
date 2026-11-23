"""Unit tests for the deterministic logging configuration (T003)."""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from code.logging_config import (
    DEFAULT_CONSOLE_LEVEL,
    DEFAULT_FILE_LEVEL,
    LOG_BACKUP_COUNT,
    LOG_MAX_BYTES,
    setup,
)


@pytest.fixture()
def isolated_log(tmp_path, monkeypatch):
    """Configure logging to a temp file and restore state afterwards."""
    log_file = tmp_path / "logs" / "run.log"
    logger = setup(log_file=log_file, force=True)
    yield logger, log_file
    # Remove handlers so other tests are unaffected.
    for handler in list(logging.getLogger().handlers):
        logging.getLogger().removeHandler(handler)
        handler.close()


def test_setup_creates_run_log(isolated_log):
    logger, log_file = isolated_log
    logging.info("hello-run-log")
    for handler in logging.getLogger().handlers:
        handler.flush()
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "hello-run-log" in content
    # Formatted message must contain level and logger metadata.
    assert "INFO" in content
    assert "root" in content


def test_console_handler_at_warning(isolated_log):
    _, _ = isolated_log
    handlers = logging.getLogger().handlers
    console = [h for h in handlers if not isinstance(h, RotatingFileHandler)]
    assert len(console) == 1
    assert console[0].level == DEFAULT_CONSOLE_LEVEL == logging.WARNING


def test_file_handler_level_and_rotation(isolated_log):
    _, _ = isolated_log
    file_handlers = [
        h for h in logging.getLogger().handlers
        if isinstance(h, RotatingFileHandler)
    ]
    assert len(file_handlers) == 1
    fh = file_handlers[0]
    assert fh.level == DEFAULT_FILE_LEVEL == logging.INFO
    assert fh.maxBytes == LOG_MAX_BYTES
    assert fh.backupCount == LOG_BACKUP_COUNT


def test_setup_is_idempotent(isolated_log):
    logger, log_file = isolated_log
    n_handlers = len(logging.getLogger().handlers)
    setup(log_file=log_file)  # second call without force
    assert len(logging.getLogger().handlers) == n_handlers


def test_console_suppresses_info(isolated_log, capsys):
    _, _ = isolated_log
    logging.info("info-should-not-appear-on-console")
    logging.warning("warn-should-appear-on-console")
    captured = capsys.readouterr()
    assert "info-should-not-appear-on-console" not in captured.err
    assert "warn-should-appear-on-console" in captured.err


def test_default_log_path_is_project_run_log():
    from code.logging_config import get_log_path, PROJECT_ROOT
    assert get_log_path() == PROJECT_ROOT / "logs" / "run.log"


def test_setup_rejects_non_path_log_file():
    import types
    with pytest.raises(TypeError):
        setup(log_file=types.ModuleType("not_a_path"), force=True)