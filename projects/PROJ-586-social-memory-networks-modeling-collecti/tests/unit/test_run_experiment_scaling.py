"""
Unit tests for the scaling mode of ``run_experiment.py``.

The tests verify that invoking the script with ``--agents 3,5,7`` and
``--plot scaling`` produces the expected CSV files without raising
exceptions.
"""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # points to repository root

@pytest.mark.parametrize(
    "agents,context,games,plot",
    [
        ("3,5,7", "full", 800, "scaling"),
    ],
)
def test_scaling_simulation_creates_files(agents, context, games, plot):
    """
    Run the experiment script in scaling mode and assert that the expected
    output files exist.
    """
    script = PROJECT_ROOT / "code" / "run_experiment.py"
    output_dir = (
        PROJECT_ROOT
        / "projects"
        / "PROJ-586-social-memory-networks-modeling-collecti"
        / "results"
    )
    # Ensure a clean start
    if output_dir.exists():
        for child in output_dir.iterdir():
            child.unlink()
    else:
        output_dir.mkdir(parents=True)

    cmd = [
        sys.executable,
        str(script),
        "--agents",
        agents,
        "--context",
        context,
        "--games",
        str(games),
        "--plot",
        plot,
    ]

    # Execute the script; it should exit with code 0.
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expect three per‑agent CSV files plus the combined scaling CSV.
    for count in [3, 5, 7]:
        expected = output_dir / f"results_{context}_{count}.csv"
        assert expected.is_file(), f"Missing {expected}"

    combined = output_dir / "scaling_results.csv"
    assert combined.is_file(), "Missing combined scaling_results.csv"