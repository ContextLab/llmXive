"""Unit tests for the RuntimeGuard utility."""
import time
from unittest import mock

import pytest

from src.utils.runtime_guard import RuntimeGuard, EPOCH_TIME_WARN, TOTAL_TIME_LIMIT

def test_epoch_warning(monkeypatch):
    guard = RuntimeGuard()
    # Simulate a long epoch (>30 min)
    guard.epoch_started()
    monkeypatch.setattr(time, "time", lambda: guard.epoch_start + EPOCH_TIME_WARN + 1)
    with mock.patch("src.utils.runtime_guard.log") as fake_log:
        guard.epoch_finished()
    fake_log.warning.assert_called_once()

def test_total_time_halt(monkeypatch):
    guard = RuntimeGuard()
    guard.epoch_started()
    # Simulate total runtime >6 h
    monkeypatch.setattr(time, "time", lambda: guard.start_time + TOTAL_TIME_LIMIT + 1)
    with mock.patch("src.utils.runtime_guard.log") as fake_log:
        with pytest.raises(RuntimeError, match="Total runtime limit exceeded"):
            guard.epoch_finished()
    fake_log.error.assert_called_once()
