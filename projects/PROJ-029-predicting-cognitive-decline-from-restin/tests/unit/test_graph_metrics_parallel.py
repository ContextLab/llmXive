"""Unit test for the parallelised graph‑metric computation.

The test checks that ``code/03_compute_graph_metrics.main`` creates the
expected output files without raising an exception.  It uses a tiny
synthetic dataset (two subjects with 3 × 3 matrices) to keep runtime tiny
while still exercising the Parallel code path.
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module under test.
from code import _03_compute_graph_metrics as gm

@pytest.fixture
def synthetic_data(tmp_path: Path):
    """Create a minimal synthetic data layout required by the pipeline."""
    # 1️⃣ eligible_subjects.csv
    eligible_dir = Path("data/processed")
    eligible_dir.mkdir(parents=True, exist_ok=True)
    eligible_path = eligible_dir / "eligible_subjects.csv"
    df = pd.DataFrame({"subject_id": ["sub-01", "sub-02"]})
    df.to_csv(eligible_path, index=False)

    # 2️⃣ connectivity matrices (tiny 3×3 symmetric matrices)
    conn_dir = Path("data/processed/connectivity_matrices")
    conn_dir.mkdir(parents=True, exist_ok=True)
    for sub in df["subject_id"]:
        mat = np.array([[1, 0.2, 0.1],
                        [0.2, 1, 0.3],
                        [0.1, 0.3, 1]])
        np.save(conn_dir / f"{sub}.npy", mat)

    yield

    # Cleanup after test.
    shutil.rmtree("data", ignore_errors=True)

def test_parallel_graph_metrics_produces_output(synthetic_data):
    """Run the main function and assert expected files exist."""
    # Ensure a clean state.
    for p in ["data/processed/graph_metrics.csv",
              "data/processed/graph_metrics_timing.txt"]:
        if Path(p).exists():
            Path(p).unlink()

    # Execute the pipeline.
    gm.main()

    # Verify CSV output.
    csv_path = Path("data/processed/graph_metrics.csv")
    assert csv_path.is_file(), "graph_metrics.csv was not created"

    df = pd.read_csv(csv_path)
    # Expect two rows (one per synthetic subject) and the required columns.
    assert len(df) == 2
    expected_cols = {
        "subject_id",
        "degree_centrality",
        "global_efficiency",
        "clustering_coefficient",
        "local_efficiency",
        "average_shortest_path_length",
    }
    assert expected_cols.issubset(set(df.columns))

    # Verify timing file.
    timing_path = Path("data/processed/graph_metrics_timing.txt")
    assert timing_path.is_file(), "Timing report not created"
    content = timing_path.read_text()
    # The file should contain a numeric runtime value.
    assert "Total runtime (seconds):" in content
    # Simple sanity check: runtime should be a positive float.
    runtime_str = content.split(":")[1].strip()
    runtime = float(runtime_str)
    assert runtime > 0.0