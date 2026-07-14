"""Unit test for the GNN training script.

The test only verifies that the script runs without error and produces the
expected CSV file with the correct columns.  It does **not** check model
performance – the metric values are derived from the real dataset.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

# Import the script's ``main`` function directly.
from training.train_gnn import main as train_gnn_main


@pytest.fixture(scope="module")
def run_training(tmp_path_factory):
    """Execute the training script in a temporary directory."""
    # Use a temporary results directory to avoid polluting the repository.
    output_dir = tmp_path_factory.mktemp("results")
    # Monkey‑patch the arguments that ``parse_args`` would read.
    # We rely on the default data location (data/processed) which should
    # already contain ``molecules_10k.parquet`` after the earlier tasks.
    # The script respects the ``--output-dir`` flag, so we point it to the
    # temporary location.
    import sys

    sys.argv = [
        "train_gnn.py",
        "--output-dir",
        str(output_dir),
        "--epochs",
        "5",  # keep the test fast
        "--patience",
        "2",
        "--seeds",
        "0",
        "1",
    ]
    train_gnn_main()
    return output_dir


def test_metrics_file_exists(run_training: Path):
    csv_path = run_training / "gnn_metrics.csv"
    assert csv_path.is_file(), "Metrics CSV was not created"


def test_metrics_file_structure(run_training: Path):
    csv_path = run_training / "gnn_metrics.csv"
    with csv_path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["seed", "model", "mae", "rmse"]
        rows = list(reader)
        # Expect two seed rows + one variance row
        assert len(rows) == 3
        # Verify that the variance row has the correct identifier
        variance_row = rows[-1]
        assert variance_row[0] == "variance"
        # The RMSE variance should be a valid float string
        try:
            float(variance_row[3])
        except ValueError:
            pytest.fail("RMSE variance column is not a valid float")