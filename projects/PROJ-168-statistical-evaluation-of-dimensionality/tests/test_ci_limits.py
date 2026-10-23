"""
Test for the CI limits checker (code/ci_limits.py).

This test verifies that the script exits with a non‑zero status code when
the monitoring CSV violates the defined resource limits.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# The llmxive_toolkit.paths module provides the `results` helper used by
# `ci_limits.py`. We monkey‑patch it so the script reads a temporary CSV
# that we control.
import llmxive_toolkit


@pytest.fixture
def violating_monitoring_csv(tmp_path):
    """Create a temporary monitoring CSV that exceeds both limits."""
    csv_path = tmp_path / "monitoring.csv"
    # Exceed RAM (>7 GB) and wall‑time (>21 600 s)
    csv_path.write_text(
        "step,wall_time_s,peak_ram_bytes\\n"
        "violation,30000,8000000000\\n"
    )
    return csv_path


def test_ci_limits_violations(monkeypatch, violating_monitoring_csv):
    """
    Run `code/ci_limits.py` with a violating CSV and assert exit code 1.
    """
    # Monkey‑patch llmxive_toolkit.paths.results to return our temp CSV.
    monkeypatch.setattr(
        llmxive_toolkit.paths,
        "results",
        lambda *args, **kwargs: violating_monitoring_csv,
    )

    script_path = Path(__file__).parents[1] / "code" / "ci_limits.py"

    # Execute the script as a subprocess using the same interpreter.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    # The script should detect the violations and exit with code 1.
    assert result.returncode == 1, (
        f"Expected exit code 1 for violating CSV, got {result.returncode}. "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )

    # The error messages should mention both SC‑003 and SC‑004.
    assert "SC-003 violation" in result.stderr
    assert "SC-004 violation" in result.stderr


def test_ci_limits_compliant(monkeypatch, tmp_path):
    """
    Ensure the script returns 0 when the CSV is within limits.
    """
    csv_path = tmp_path / "monitoring.csv"
    csv_path.write_text(
        "step,wall_time_s,peak_ram_bytes\\n"
        "ok_step,10,1000000\\n"
    )

    monkeypatch.setattr(
        llmxive_toolkit.paths,
        "results",
        lambda *args, **kwargs: csv_path,
    )

    script_path = Path(__file__).parents[1] / "code" / "ci_limits.py"

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Expected exit code 0 for compliant CSV, got {result.returncode}. "
        f"Stdout: {result.stdout}\\nStderr: {result.stderr}"
    )
    assert "CI limits check passed" in result.stdout