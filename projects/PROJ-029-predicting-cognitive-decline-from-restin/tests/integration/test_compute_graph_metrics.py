"""Integration test that runs the graph‑metric script on a tiny synthetic dataset."""

import os
import numpy as np
from pathlib import Path

import pytest

# Import the script’s main function
from code import _03_compute_graph_metrics as compute_script


@pytest.fixture
def synthetic_data(tmp_path: Path):
    """Create a minimal set of connectivity matrices and an eligible subjects CSV."""
    processed = tmp_path / "data" / "processed"
    conn_dir = processed / "connectivity"
    conn_dir.mkdir(parents=True)

    # Create two synthetic subjects
    subjects = ["sub-001", "sub-002"]
    for sid in subjects:
        mat = np.eye(90)  # simple identity matrix as placeholder
        np.save(conn_dir / f"{sid}.npy", mat)

    # Write eligible_subjects.csv
    eligible_csv = processed / "eligible_subjects.csv"
    with eligible_csv.open("w", newline="") as f:
        f.write("subject_id\\n")
        for sid in subjects:
            f.write(f"{sid}\\n")

    return {
        "processed_dir": processed,
        "eligible_csv": eligible_csv,
        "conn_dir": conn_dir,
    }


def test_compute_graph_metrics_runs_successfully(synthetic_data, monkeypatch):
    """Run the script and verify it produces a non‑empty CSV."""
    # Monkey‑patch the cwd so the script resolves paths relative to the tmp directory.
    monkeypatch.chdir(synthetic_data["processed_dir"].parent.parent)  # project root

    exit_code = compute_script.main()
    assert exit_code == 0

    output_csv = synthetic_data["processed_dir"] / "graph_metrics.csv"
    assert output_csv.is_file()

    # Basic sanity check on the CSV contents
    with output_csv.open() as f:
        lines = f.readlines()
    # Header + two rows expected
    assert len(lines) == 3
    header = lines[0].strip().split(",")
    expected_header = [
        "subject_id",
        "avg_degree",
        "global_efficiency",
        "avg_clustering",
        "avg_path_length",
    ]
    assert header == expected_header
    # Ensure subject IDs appear
    rows = [line.strip().split(",")[0] for line in lines[1:]]
    assert set(rows) == {"sub-001", "sub-002"}