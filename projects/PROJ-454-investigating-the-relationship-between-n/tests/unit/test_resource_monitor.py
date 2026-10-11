"""Unit tests for utils/resource_monitor.py (Task T004)."""
import logging
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE_DIR))

from utils import resource_monitor as rm


def test_memory_usage_positive():
    assert rm.get_memory_usage_gb() > 0


def test_disk_usage_nonnegative():
    assert rm.get_disk_usage_gb() >= 0


def test_check_resource_limits_returns_bool():
    assert isinstance(rm.check_resource_limits(), bool)


def test_check_limits_with_tiny_thresholds_fails():
    # A 1-byte RAM limit can never be satisfied by a live process.
    assert rm.check_resource_limits(ram_limit_gb=1e-9) is False


def test_enforce_limits_raises_when_exceeded():
    with pytest.raises(rm.ResourceLimitExceeded):
        rm.enforce_limits(ram_limit_gb=1e-9)


def test_enforce_limits_passes_with_generous_limits():
    rm.enforce_limits(ram_limit_gb=1e6, disk_limit_gb=1e6)


def test_log_resource_snapshot_writes_log_file():
    snap = rm.log_resource_snapshot(label="unit_test")
    assert snap["label"] == "unit_test"
    assert "ram_gb" in snap and "disk_gb" in snap
    assert rm.LOG_FILE.exists()
    content = rm.LOG_FILE.read_text()
    assert "unit_test" in content


def test_log_resource_snapshot_accepts_logger_and_positional_label():
    logger = logging.getLogger("test_rm")
    snap = rm.log_resource_snapshot(logger, "positional_label")
    assert snap["label"] == "positional_label"


def test_log_resource_usage():
    snap = rm.log_resource_usage(logging.getLogger("test_rm"), "step", ram_gb=1.5)
    assert snap["ram_gb"] == 1.5


def test_record_aborts_when_over_limit(monkeypatch):
    monkeypatch.setattr(rm, "get_memory_usage_gb", lambda: 99.0)
    with pytest.raises(rm.ResourceLimitExceeded):
        rm.record("over_limit")


def test_record_ok(monkeypatch):
    monkeypatch.setattr(rm, "get_memory_usage_gb", lambda: 0.5)
    monkeypatch.setattr(rm, "get_disk_usage_gb", lambda: 0.5)
    snap = rm.record("ok_case")
    assert snap["ram_gb"] == 0.5


def test_main_self_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = rm.main(["--self-check", "--label", "cli_test"])
    assert rc == 0
    assert rm.LOG_FILE.exists()