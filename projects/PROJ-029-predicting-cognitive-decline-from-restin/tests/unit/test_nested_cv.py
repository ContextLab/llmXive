"""Unit tests for the nested‑CV logic in ``code/04_train_model.py``."""

import pandas as pd
import numpy as np
import pytest

from code import _04_train_model as train_mod

@pytest.fixture
def synthetic_data(tmp_path):
    """Create a tiny synthetic dataset that mimics the expected schema."""
    # 30 subjects, 25 graph‑metric features
    rng = np.random.default_rng(42)
    X = pd.DataFrame(rng.normal(size=(30, 25)),
                     columns=[f"metric_{i}" for i in range(25)])
    # Add a subject_id column
    X.insert(0, "subject_id", [f"sub-{i:03d}" for i in range(30)])

    # Simulate baseline/follow‑up scores with a modest decline in ~30% of subjects
    scores = pd.DataFrame({
        "subject_id": X["subject_id"],
        "mmse_baseline": rng.integers(28, 30, size=30),
        "mmse_followup": rng.integers(24, 30, size=30),
    })

    # Write to the expected locations
    (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
    X_path = tmp_path / "data" / "processed" / "graph_metrics.csv"
    scores_path = tmp_path / "data" / "processed" / "eligible_subjects.csv"
    X.to_csv(X_path, index=False)
    scores.to_csv(scores_path, index=False)
    return tmp_path

def test_train_and_evaluate_nested_cv(monkeypatch, synthetic_data):
    """Run the full pipeline on the synthetic data and check outputs."""
    # Patch Path objects inside the module to point at the temporary directory
    monkeypatch.setattr(train_mod, "Path", lambda *p: synthetic_data / Path(*p))

    # Execute main – it should return 0 and produce the two artefacts
    assert train_mod.main() == 0
    # Verify model file exists
    model_path = synthetic_data / "data" / "processed" / "model.pkl"
    assert model_path.is_file()
    # Verify performance report exists and contains expected keys
    report_path = synthetic_data / "data" / "processed" / "performance_report.json"
    assert report_path.is_file()
    report = pd.read_json(report_path, typ="series")
    assert "mean_roc_auc" in report
    assert "best_params" in report