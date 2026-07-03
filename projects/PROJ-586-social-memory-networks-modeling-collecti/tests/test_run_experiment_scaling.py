"""Integration test for the scaling mode of run_experiment."""

import csv
import os
from pathlib import Path

import pytest

from run_experiment import main


@pytest.fixture
def tmp_output(tmp_path: Path):
    """Provide temporary file paths for the CSV outputs."""
    detailed = tmp_path / "detailed_scaling.csv"
    scaling = tmp_path / "scaling_data.csv"
    return detailed, scaling


def test_scaling_experiment_writes_files(tmp_output):
    detailed_path, scaling_path = tmp_output
    # Run the script in scaling mode
    exit_code = main(
        [
            "--scaling",
            "--output",
            str(detailed_path),
            "--scaling-output",
            str(scaling_path),
        ]
    )
    assert exit_code == 0
    # Verify detailed CSV exists and has the right number of rows (3 agents * 800 games)
    assert detailed_path.is_file()
    with detailed_path.open() as f:
        rows = list(csv.reader(f))
    # Header + 3*800 rows
    assert len(rows) == 1 + 3 * 800

    # Verify scaling CSV exists and contains three aggregated rows
    assert scaling_path.is_file()
    with scaling_path.open() as f:
        rows = list(csv.reader(f))
    assert len(rows) == 1 + 3  # header + three agent counts
    header = rows[0]
    assert header == ["agent_count", "mean_specialization", "mean_retrieval"]
    # Check that agent counts are exactly 3,5,7
    agent_counts = [int(r[0]) for r in rows[1:]]
    assert agent_counts == [3, 5, 7]