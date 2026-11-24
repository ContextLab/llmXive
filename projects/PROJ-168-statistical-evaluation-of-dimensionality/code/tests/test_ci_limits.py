"""Tests for the ci_limits.py script.

The tests write a temporary `results/monitoring.csv` file,
invoke the script via a subprocess, and check the exit code.
"""
import sys
import subprocess
import pandas as pd
from llmxive_toolkit import paths

def _write_monitoring(df: pd.DataFrame):
    """Write the provided DataFrame to the expected monitoring CSV path."""
    out_path = paths.results("monitoring.csv")
    df.to_csv(out_path, index=False)
    return out_path

def test_ci_limits_violates():
    """A CSV that exceeds the RAM limit should cause exit code 1."""
    df = pd.DataFrame(
        {
            "step": ["step1", "step2"],
            "wall_time_s": [10_000, 12_000],
            "peak_ram_bytes": [8_000_000_000, 6_000_000_000],
        }
    )
    _write_monitoring(df)

    result = subprocess.run(
        [sys.executable, str(paths.code("ci_limits.py"))],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "SC-003 violation" in result.stderr

def test_ci_limits_passes():
    """A CSV within limits should exit with code 0."""
    df = pd.DataFrame(
        {
            "step": ["step1", "step2"],
            "wall_time_s": [5_000, 6_000],
            "peak_ram_bytes": [2_000_000_000, 3_000_000_000],
        }
    )
    _write_monitoring(df)

    result = subprocess.run(
        [sys.executable, str(paths.code("ci_limits.py"))],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # No violation messages should be printed
    assert result.stderr == ""