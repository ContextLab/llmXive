"""Unit test ensuring that the parallel implementation produces the same
number of rows as there are input subjects and that the output CSV is
written."""

import csv
from pathlib import Path

import pandas as pd
import pytest

# Import the functions we need from the module under test
from code import (
    compute_subject_metrics,
    write_outputs,
    load_subject_list,
    load_config_wrapper,
    get_data_directories,
)

@pytest.fixture
def dummy_processed_dir(tmp_path: Path):
    """Create a minimal processed directory with an empty eligible_subjects.csv."""
    processed = tmp_path / "processed"
    processed.mkdir()
    # Write a tiny eligible_subjects.csv with two dummy IDs
    csv_path = processed / "eligible_subjects.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["subject_id"])
        writer.writerow(["001"])
        writer.writerow(["002"])
    return processed

@pytest.fixture
def dummy_raw_dir(tmp_path: Path):
    """Create a raw directory containing dummy connectivity matrices."""
    raw = tmp_path / "raw" / "ds000246"
    raw.mkdir(parents=True)
    for sid in ("001", "002"):
        sub_dir = raw / f"sub-{sid}" / "func"
        sub_dir.mkdir(parents=True)
        matrix_path = sub_dir / f"sub-{sid}_desc-connectivity_matrix.npy"
        # Simple identity matrix as a stand‑in
        import numpy as np
        np.save(matrix_path, np.identity(90))
    return raw

def test_parallel_computation_writes_csv(
    dummy_processed_dir: Path, dummy_raw_dir: Path
):
    # Load config using the real helper – we patch the paths afterwards
    cfg = load_config_wrapper()
    cfg["raw_data_dir"] = str(dummy_raw_dir.parent.parent)  # points to project root
    cfg["processed_dir"] = str(dummy_processed_dir.parent)

    raw_dir, processed_dir = get_data_directories(cfg)

    subject_ids = load_subject_list(processed_dir)
    assert subject_ids == ["001", "002"]

    # Compute metrics (this will run the parallelised function)
    results = [
        compute_subject_metrics(raw_dir, sid) for sid in subject_ids
    ]
    assert len(results) == 2
    for r in results:
        assert r["subject_id"] in {"001", "002"}

    # Write outputs and verify the CSV exists and has the right shape
    write_outputs(processed_dir, results)
    out_csv = processed_dir / "graph_metrics.csv"
    assert out_csv.is_file()

    df = pd.read_csv(out_csv)
    assert list(df.columns) == [
        "subject_id",
        "degree_mean",
        "global_efficiency",
        "clustering_coefficient",
        "characteristic_path_length",
    ]
    assert df.shape[0] == 2