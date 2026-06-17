"""
Basic sanity test for the logging utilities introduced in T068.

The test simply checks that calling ``logger.log`` with one or two
positional arguments does not raise and that a JSON line is written
to ``data/logs.json``.
"""

import json
from pathlib import Path

from reproducibility.logs import get_logger, ReproducibilityLogger


def test_logger_flexible_signature(tmp_path, monkeypatch):
    # Redirect the log file to a temporary location.
    log_file = tmp_path / "logs.json"
    monkeypatch.setattr(
        "reproducibility.logs._LOG_FILE", log_file, raising=False
    )
    # Ensure a fresh logger instance.
    logger = ReproducibilityLogger()
    logger.log("event_one")
    logger.log("event_two", {"detail": 42})
    # Verify two JSON lines were written.
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "event" in entry
        assert "payload" in entry