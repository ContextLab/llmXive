"""
Unit tests for the ``code.metrics_logging`` module.

The tests verify that:
1. The logger creates ``data/metrics_log.txt`` if it does not exist.
2. ``log_metric_progress`` writes an INFO‑level entry containing the supplied
   message.
3. ``log_metric_exclusion`` writes a WARNING‑level entry that includes the
   subject identifier and the exclusion reason.
"""

import os
import pathlib

import pytest

from code.metrics_logging import (
    _METRICS_LOG_PATH,
    get_metrics_logger,
    log_metric_progress,
    log_metric_exclusion,
)


@pytest.fixture(autouse=True)
def clean_metrics_log(tmp_path, monkeypatch):
    """
    Ensure a clean ``metrics_log.txt`` before each test.
    The fixture rewrites the module‑level path to point inside the temporary
    directory so that the test does not interfere with any real run‑book
    output.
    """
    # Redirect the global path to a temp location.
    temp_log = tmp_path / "metrics_log.txt"
    monkeypatch.setattr(
        "code.metrics_logging._METRICS_LOG_PATH", pathlib.Path(temp_log)
    )
    # Ensure the parent directory exists.
    temp_log.parent.mkdir(parents=True, exist_ok=True)
    # Remove any pre‑existing file.
    if temp_log.is_file():
        temp_log.unlink()
    yield
    # Cleanup after test.
    if temp_log.is_file():
        temp_log.unlink()


def test_logger_creates_file():
    """The logger must create ``metrics_log.txt`` on first use."""
    logger = get_metrics_logger()
    # The logger should have at least one handler pointing to the file.
    assert any(isinstance(h, type(logger.handlers[0])) for h in logger.handlers)
    # The file must now exist.
    assert _METRICS_LOG_PATH.is_file()


def test_log_metric_progress_writes_message():
    """INFO messages should be written and contain the supplied text."""
    test_msg = "Starting sliding‑window computation for subject SUBJ01"
    log_metric_progress(test_msg)

    # Read the log file and verify content.
    content = _METRICS_LOG_PATH.read_text(encoding="utf-8")
    assert "INFO" in content
    assert test_msg in content


def test_log_metric_exclusion_writes_warning():
    """WARNING messages must include subject id and reason."""
    subject = "SUBJ02"
    reason = "FD > 0.5 mm"
    log_metric_exclusion(subject, reason)

    content = _METRICS_LOG_PATH.read_text(encoding="utf-8")
    assert "WARNING" in content
    assert subject in content
    assert reason in content