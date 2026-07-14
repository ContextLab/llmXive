"""Integration test for the end‑to‑end graph‑metric pipeline."""

import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code import __main__ as dummy  # noqa: F401  # ensure package import works

# Import the main function directly
from code import _load_module  # placeholder for dynamic import if needed

# We'll import the script as a module
import importlib.util

SPEC_PATH = Path("code/03_compute_graph_metrics.py")
spec = importlib.util.spec_from_file_location("compute_graph_metrics", SPEC_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore


@pytest.fixture(scope="function")
def setup_fake_data(tmp_path):
    """Create minimal eligible_subjects.csv and dummy matrices."""
    processed_dir = Path("data/processed")
    matrix_dir = processed_dir / "connectivity_matrices"
    # Ensure clean state
    if processed_dir.exists():
        shutil.rmtree(processed_dir)
    matrix_dir.mkdir(parents=True, exist_ok=True)

    # Write eligible subjects
    subjects = ["sub-01", "sub-02"]
    df = pd.DataFrame({"subject_id": subjects})
    df.to_csv(processed_dir / "eligible_subjects.csv", index=False)

    # Create tiny symmetric matrices for each subject
    for subj in subjects:
        mat = np.array(
            [
                [0.0, 0.8, 0.3],
                [0.8, 0.0, 0.4],
                [0.3, 0.4, 0.0],
            ]
        )
        np.save(matrix_dir / f"{subj}_matrix.npy", mat)

    yield
    # Cleanup after test
    if processed_dir.exists():
        shutil.rmtree(processed_dir)


def test_pipeline_runs_and_creates_csv(setup_fake_data):
    """Run the script’s main() and verify output CSV exists and is sane."""
    # Run the pipeline
    module.main()

    output_path = Path("data/processed/graph_metrics.csv")
    assert output_path.is_file()

    df = pd.read_csv(output_path)
    # Should have two rows matching the two subjects
    assert df.shape[0] == 2
    expected_cols = {
        "subject_id",
        "avg_degree",
        "global_efficiency",
        "avg_clustering",
        "avg_path_length",
    }
    assert set(df.columns) == expected_cols
    # No NaNs for the fabricated matrices
    assert not df.isna().any().any()