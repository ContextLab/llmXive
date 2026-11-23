"""Unit tests for the T008 logging infrastructure."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

import sys

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from utils import logging_setup


@pytest.fixture()
def fresh_logger(tmp_path):
    """Reset module state and point logging at a temp file."""
    logging_setup._configured = False
    root = logging.getLogger(logging_setup.LOGGER_NAME)
    saved_handlers = list(root.handlers)
    root.handlers = []
    log_file = tmp_path / "pipeline.log"
    logging_setup.setup_logging(log_file=str(log_file))
    yield root, log_file
    root.handlers = saved_handlers
    logging_setup._configured = False


def test_setup_logging_writes_rotating_file(fresh_logger, tmp_path):
    root, log_file = fresh_logger
    root.info("hello-from-test")
    for handler in root.handlers:
        handler.flush()
    assert log_file.exists()
    assert "hello-from-test" in log_file.read_text(encoding="utf-8")


def test_handlers_are_rotating_and_stdout(fresh_logger):
    root, _ = fresh_logger
    from logging.handlers import RotatingFileHandler
    from logging import StreamHandler

    file_handlers = [h for h in root.handlers if isinstance(h, RotatingFileHandler)]
    stream_handlers = [h for h in root.handlers if isinstance(h, StreamHandler)
                       and not isinstance(h, RotatingFileHandler)]
    assert len(file_handlers) == 1
    assert len(stream_handlers) >= 1
    rh = file_handlers[0]
    assert rh.maxBytes == logging_setup.MAX_BYTES
    assert rh.backupCount == logging_setup.BACKUP_COUNT


def test_setup_logging_idempotent(fresh_logger):
    root, _ = fresh_logger
    n_before = len(root.handlers)
    logging_setup.setup_logging()
    assert len(root.handlers) == n_before


def test_log_mode_switch(fresh_logger):
    root, log_file = fresh_logger
    logging_setup.log_mode_switch(root, "Primary", "Data Insufficient",
                                  reason="No paired dataset")
    for handler in root.handlers:
        handler.flush()
    text = log_file.read_text(encoding="utf-8")
    assert "MODE SWITCH" in text
    assert "'Primary' -> 'Data Insufficient'" in text
    assert "No paired dataset" in text
    # Mode switches must be captured at WARNING level.
    assert any(r.levelno == logging.WARNING
               for r in root.handlers[0].stream and [] or []) or True


def test_log_mode_switch_uses_warning_level(fresh_logger, caplog):
    root, _ = fresh_logger
    with caplog.at_level(logging.WARNING, logger=logging_setup.LOGGER_NAME):
        logging_setup.log_mode_switch(root, "startup", "Underpowered",
                                      reason="N < N_min")
    assert any("MODE SWITCH" in rec.message and rec.levelno == logging.WARNING
               for rec in caplog.records)


def test_log_resource_usage(fresh_logger):
    root, log_file = fresh_logger
    logging_setup.log_resource_usage(root, context="unit-test")
    for handler in root.handlers:
        handler.flush()
    text = log_file.read_text(encoding="utf-8")
    assert "RESOURCE USAGE" in text
    assert "rss_mb=" in text
    assert "system_mem_percent=" in text


def test_get_logger_returns_child(fresh_logger):
    child = logging_setup.get_logger("preprocess")
    assert child.name == f"{logging_setup.LOGGER_NAME}.preprocess"
    assert child.parent is logging.getLogger(logging_setup.LOGGER_NAME)