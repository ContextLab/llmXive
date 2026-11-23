"""
Minimal test for the pilot gate script.

The test creates temporary CSV files that mimic the expected input format,
invokes the ``main`` function, and checks that the exit code matches the
expected behaviour (pass when r >= 0.5, fail otherwise).
"""

import csv
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

# Import the script as a module
from src.experiment.pilot_gate import main as pilot_gate_main, HUMAN_RATINGS_PATH, METRICS_PATH


def write_csv(path: Path, header: list[str], rows: list[tuple]):
    """Utility to write a simple CSV file."""
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture
def temporary_data():
    """Create a temporary data directory structure with dummy CSVs."""
    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Override the module‑level paths so the script reads our temp files
        original_ratings = HUMAN_RATINGS_PATH
        original_metrics = METRICS_PATH
        try:
            # Point the module globals to the temporary files
            src_path = Path(__file__).parents[2] / "src" / "experiment"
            # Monkey‑patch the constants
            pilot_gate_module = sys.modules["src.experiment.pilot_gate"]
            pilot_gate_module.HUMAN_RATINGS_PATH = base / "human_ratings.csv"
            pilot_gate_module.METRICS_PATH = base / "metrics.csv"

            # Write placeholder files (will be overwritten by each test)
            (base / "human_ratings.csv").parent.mkdir(parents=True, exist_ok=True)
            (base / "metrics.csv").parent.mkdir(parents=True, exist_ok=True)

            yield base
        finally:
            # Restore original constants
            pilot_gate_module.HUMAN_RATINGS_PATH = original_ratings
            pilot_gate_module.METRICS_PATH = original_metrics


def test_pilot_gate_passes(temporary_data):
    """Correlation >= 0.5 should return exit code 0."""
    # Create perfectly correlated data
    rows = [(i, i) for i in range(1, 6)]
    write_csv(
        temporary_data / "human_ratings.csv",
        ["image_id", "complexity_score"],
        rows,
    )
    # Use a single metric that mirrors the rating
    write_csv(
        temporary_data / "metrics.csv",
        ["image_id", "entropy"],
        rows,
    )
    exit_code = pilot_gate_main()
    assert exit_code == 0


def test_pilot_gate_fails(temporary_data):
    """Correlation < 0.5 should return exit code 1."""
    # Human ratings increase linearly
    human_rows = [(i, i) for i in range(1, 6)]
    write_csv(
        temporary_data / "human_ratings.csv",
        ["image_id", "complexity_score"],
        human_rows,
    )
    # Metrics are constant, leading to zero correlation
    metric_rows = [(i, 10) for i in range(1, 6)]
    write_csv(
        temporary_data / "metrics.csv",
        ["image_id", "entropy"],
        metric_rows,
    )
    exit_code = pilot_gate_main()
    assert exit_code == 1