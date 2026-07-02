"""Basic integration test for ``code/run_experiment.py``.

The test invokes the script with a very small number of games to ensure that
it runs end‑to‑end without raising exceptions and that the expected CSV file
is produced.  The test does **not** validate metric values – those are
produced by the actual simulation code and are therefore nondeterministic
beyond the fixed random seed.
"""

import sys
from pathlib import Path
import subprocess

import pytest

# The script should be importable and callable via ``python -m`` as well.
SCRIPT = Path(__file__).resolve().parents[2] / "run_experiment.py"

@pytest.mark.parametrize(
    "agents,games,context,expected_file",
    [
        ("2", "5", "full", "results_full.csv"),
        ("3,4", "3", "limited", "results_limited.csv"),
    ],
)
def test_run_experiment_cli(tmp_path, agents, games, context, expected_file):
    output_dir = tmp_path / "results"
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--context",
        context,
        "--agents",
        agents,
        "--games",
        games,
        "--output-dir",
        str(output_dir),
        "--seed",
        "123",
    ]

    # Run the script; it should exit with code 0
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # Verify that the CSV file exists and has the correct header
    csv_path = output_dir / expected_file
    assert csv_path.is_file(), f"Missing CSV: {csv_path}"

    with csv_path.open() as f:
        header = f.readline().strip()
    expected_header = (
        "game_id,specialization_index,retrieval_efficiency,context_condition,agent_count"
    )
    assert header == expected_header, f"Unexpected CSV header: {header}"