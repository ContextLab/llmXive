"""
Unit tests for the termination signal emission logic.

These tests verify that the memory‑limit detection function in
``src.cli.run_simulation`` correctly signals an out‑of‑bounds condition
and writes a status JSON file containing a reason for termination.
"""

import json
from pathlib import Path

import pytest

# The module under test provides ``check_memory_and_log`` and
# ``get_memory_usage_mb``.  We monkey‑patch ``get_memory_usage_mb`` to
# simulate a memory‑exhaustion scenario.
import src.cli.run_simulation as run_simulation


def test_memory_limit_triggers_signal(monkeypatch, tmp_path: Path):
    """
    Simulate a situation where memory usage far exceeds any realistic limit.
    The ``check_memory_and_log`` function should detect this, write a JSON
    status file, and return ``True`` to indicate that the limit was hit.
    """

    # Force ``get_memory_usage_mb`` to return a huge value.
    monkeypatch.setattr(
        run_simulation,
        "get_memory_usage_mb",
        lambda: 1_000_000.0,  # 1 TB – well above any CI runner limit
    )

    # Use a temporary file for the status log.
    log_file = tmp_path / "simulation_status.json"

    # The function should return ``True`` indicating the limit was exceeded.
    limit_exceeded = run_simulation.check_memory_and_log(str(log_file))
    assert limit_exceeded is True

    # The log file must exist and contain valid JSON.
    assert log_file.is_file()
    with log_file.open("r", encoding="utf-8") as f:
        status = json.load(f)

    # The JSON payload should include a clear reason for termination.
    # The exact wording is defined by the implementation; we only require
    # that a ``reason`` field exists and mentions memory.
    assert "reason" in status
    assert "memory" in status["reason"].lower()