"""Basic integration test for the run_experiment CLI."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.timeout(60)
def test_run_experiment_full_context(tmp_path: Path):
    """Run the experiment with a small configuration and verify CSV output."""
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "code/run_experiment.py",
        "--context",
        "full",
        "--agents",
        "2,3",
        "--games",
        "5",
        "--output-dir",
        str(output_dir),
    ]
    # Execute the script
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify that the CSV file was created
    csv_path = output_dir / "results_full.csv"
    assert csv_path.is_file(), "Results CSV was not created"

    # Basic sanity check on CSV contents
    lines = csv_path.read_text().splitlines()
    # Header + 2 agents * 5 games = 11 lines
    assert len(lines) == 1 + 2 * 5, "Unexpected number of CSV rows"

    # Verify required columns exist
    header = lines[0].split(",")
    for col in ["game_id", "context_condition", "agent_count"]:
        assert col in header, f"Missing expected column {col}"

# The limited‑context mode requires thresholds; test it minimally
@pytest.mark.timeout(60)
def test_run_experiment_limited_context(tmp_path: Path):
    output_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        "code/run_experiment.py",
        "--context",
        "limited",
        "--agents",
        "2",
        "--games",
        "3",
        "--thresholds",
        "128,256",
        "--output-dir",
        str(output_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    csv_path = output_dir / "results_limited.csv"
    assert csv_path.is_file(), "Limited‑context CSV not created"
    lines = csv_path.read_text().splitlines()
    # Header + 1 agent * 3 games = 4 lines
    assert len(lines) == 1 + 3, "Unexpected number of rows for limited context"