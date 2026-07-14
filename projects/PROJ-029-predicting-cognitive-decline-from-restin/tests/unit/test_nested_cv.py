"""Unit tests for the nested CV pipeline defined in code/04_train_model.py.

The tests use a tiny synthetic dataset to verify that:
  * The pipeline runs without raising.
  * The output performance report contains the expected keys.
  * The model file is written to the correct location.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from code import _04_train_model as train_mod

@pytest.fixture(scope="module")
def synthetic_data(tmp_path_factory):
    """Create minimal synthetic CSVs that mimic the real inputs."""
    # eligible_subjects.csv
    elig = pd.DataFrame({
        "subject_id": [f"sub-{i:03d}" for i in range(1, 11)],
        "mmse_t1": [30] * 10,
        "mmse_t2": [28, 30, 27, 30, 29, 30, 30, 30, 30, 30],
        "moca_t1": [28] * 10,
        "moca_t2": [28] * 10,
    })
    # graph_metrics.csv – 5 dummy features per subject
    metrics = pd.DataFrame({
        "subject_id": elig["subject_id"],
        "feat_a": range(10),
        "feat_b": range(10, 20),
        "feat_c": range(20, 30),
        "feat_d": range(30, 40),
        "feat_e": range(40, 50),
    })
    data_dir = Path("data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)
    elig_path = data_dir / "eligible_subjects.csv"
    metrics_path = data_dir / "graph_metrics.csv"
    elig.to_csv(elig_path, index=False)
    metrics.to_csv(metrics_path, index=False)
    yield
    # Cleanup after tests
    for p in [elig_path, metrics_path, Path("data/processed/model.pkl"), Path("data/processed/performance_report.json")]:
        if p.is_file():
            p.unlink()

def test_nested_cv_runs_and_produces_outputs(synthetic_data):
    """Run the full main() and check that artifacts exist and are well‑formed."""
    # Execute the training script
    train_mod.main()

    # Verify model file
    model_path = Path("data/processed/model.pkl")
    assert model_path.is_file(), "Model file was not created"

    # Verify performance report
    report_path = Path("data/processed/performance_report.json")
    assert report_path.is_file(), "Performance report was not created"
    with report_path.open() as f:
        report = json.load(f)
    # Basic sanity checks on the report structure
    assert "fold_metrics" in report
    assert "mean_metrics" in report
    assert isinstance(report["fold_metrics"], list)
    assert isinstance(report["mean_metrics"], dict)

# The synthetic dataset is tiny; we only care that the pipeline runs without error.
# No need for heavy metric assertions.