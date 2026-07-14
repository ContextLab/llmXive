"""Unit test to ensure that the parallel implementation in
``code/03_compute_graph_metrics.py`` produces the expected number of rows
and includes required columns.

The test creates a tiny synthetic eligibility list and corresponding
dummy connectivity matrices, runs the main function, and checks the
output CSV.
"""

import csv
from pathlib import Path

import pytest

# Import the module under test
from code import _03_compute_graph_metrics as gmetrics

@pytest.fixture
def setup_dummy_data(tmp_path: Path):
    # Create dummy eligible_subjects.csv
    eligible_path = Path("data/processed/eligible_subjects.csv")
    eligible_path.parent.mkdir(parents=True, exist_ok=True)
    with eligible_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["subject_id"])
        writer.writeheader()
        writer.writerow({"subject_id": "sub-001"})
        writer.writerow({"subject_id": "sub-002"})

    # Create dummy connectivity matrices (90x90 zeros)
    matrix_dir = Path("data/processed")
    for sid in ["sub-001", "sub-002"]:
        matrix_path = matrix_dir / f"{sid}_matrix.json"
        matrix = [[0.0] * 90 for _ in range(90)]
        with matrix_path.open("w") as jf:
            import json
            json.dump(matrix, jf)

    yield

    # Cleanup after test
    for p in [eligible_path, *matrix_dir.glob("*_matrix.json")]:
        p.unlink()
    if eligible_path.parent.exists():
        eligible_path.parent.rmdir()

def test_parallel_graph_metrics_produces_output(setup_dummy_data, tmp_path):
    # Run the main pipeline
    gmetrics.main()

    output_path = Path("data/processed/graph_metrics.csv")
    assert output_path.is_file(), "graph_metrics.csv was not created"

    with output_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Expect two rows (one per subject)
    assert len(rows) == 2
    # Verify required columns exist
    expected_cols = {
        "subject_id",
        "degree_mean",
        "global_efficiency",
        "clustering_coefficient",
        "characteristic_path_length",
    }
    assert expected_cols.issubset(set(reader.fieldnames))      

# The test file is intentionally lightweight to keep CI runtime low.