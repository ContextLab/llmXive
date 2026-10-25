"""
Unit tests for ``RuntimeGuard``.

The guard should abort with exit code 143 when the deadline is in the
past and write a JSON‑lines ``timeout`` event to ``logs/timeout.log``.
"""
import sys
import time
import json
from pathlib import Path

import pytest

from src.pipeline.runtime_guard import RuntimeGuard

def test_runtime_guard_exits_on_past_deadline(tmp_path, monkeypatch):
    # Use a temporary log file to avoid polluting the real logs directory.
    temp_log = tmp_path / "timeout.log"
    monkeypatch.setattr(
        "src.pipeline.runtime_guard._TIMEOUT_LOG_PATH", temp_log, raising=False
    )

    # Deadline 10 seconds in the past.
    past_deadline = time.time() - 10
    guard = RuntimeGuard(deadline_ts=past_deadline)

    # The guard should raise SystemExit with code 143.
    with pytest.raises(SystemExit) as exc:
        guard.check()
    assert exc.value.code == 143

    # Verify that a timeout event was written.
    assert temp_log.is_file()
    lines = temp_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event"] == "timeout"

def test_runtime_guard_no_exit_when_before_deadline(tmp_path, monkeypatch):
    # Redirect log path but the deadline is in the future.
    temp_log = tmp_path / "timeout.log"
    monkeypatch.setattr(
        "src.pipeline.runtime_guard._TIMEOUT_LOG_PATH", temp_log, raising=False
    )

    future_deadline = time.time() + 60  # 1 minute ahead
    guard = RuntimeGuard(deadline_ts=future_deadline)

    # Should not raise.
    guard.check()
    # No timeout file should be created.
    assert not temp_log.exists()