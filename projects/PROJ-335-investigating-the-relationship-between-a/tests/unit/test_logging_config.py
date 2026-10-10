"""Unit tests for the T008 structured logging infrastructure."""

import json
import logging
from pathlib import Path

from utils.logging_config import (
    DEFAULT_LOG_FILE,
    StructuredFormatter,
    get_logger,
    log_metric,
    setup_logging,
)


def _make_record(msg: str, **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_structured_formatter_emits_valid_json():
    fmt = StructuredFormatter()
    line = fmt.format(_make_record("hello", event="download", dataset="ds000248"))
    parsed = json.loads(line)
    assert parsed["message"] == "hello"
    assert parsed["level"] == "INFO"
    assert parsed["event"] == "download"
    assert parsed["dataset"] == "ds000248"
    assert "timestamp" in parsed


def test_structured_formatter_handles_non_serializable_extra():
    fmt = StructuredFormatter()
    line = fmt.format(_make_record("obj", payload=object()))
    parsed = json.loads(line)
    assert "payload" in parsed


def test_setup_logging_writes_file_and_console(tmp_path, capsys):
    logger = setup_logging(
        log_dir=str(tmp_path), log_file="test.log", logger_name="t008.test"
    )
    logger.info("file message", extra={"event": "test"})
    for handler in logger.handlers:
        handler.flush()
    log_file = tmp_path / "test.log"
    assert log_file.exists()
    lines = [
        json.loads(l)
        for l in log_file.read_text().strip().splitlines()
    ]
    assert any(entry["message"] == "file message" for entry in lines)
    captured = capsys.readouterr()
    assert "file message" in captured.err


def test_get_logger_returns_logger():
    logger = get_logger("t008.get")
    assert isinstance(logger, logging.Logger)
    assert get_logger("t008.get") is logger


def test_log_metric_writes_structured_entry(tmp_path):
    logger = setup_logging(
        log_dir=str(tmp_path), log_file="metrics.log", logger_name="t008.metric"
    )
    log_metric(logger, "alpha_power_Pz", 0.42, subject="sub-01")
    for handler in logger.handlers:
        handler.flush()
    entries = [
        json.loads(l)
        for l in (tmp_path / "metrics.log").read_text().strip().splitlines()
    ]
    metric_entries = [e for e in entries if e.get("event") == "metric"]
    assert metric_entries
    entry = metric_entries[-1]
    assert entry["metric"] == "alpha_power_Pz"
    assert entry["value"] == 0.42
    assert entry["subject"] == "sub-01"