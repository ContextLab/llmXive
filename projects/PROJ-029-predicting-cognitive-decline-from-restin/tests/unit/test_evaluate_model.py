"""Unit tests for ``code/05_evaluate_model.py``.

The tests create a tiny synthetic dataset, invoke the core functions and
verify that the JSON report is produced with the expected structure.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module under test
import importlib.util

spec = importlib.util.spec_from_file_location(
    "evaluate_model", Path("code/05_evaluate_model.py")
)
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)  # type: ignore

# Helper to create minimal CSV fixtures
def _create_dummy_data(tmp_path: Path):
    # Create a tiny eligible subjects CSV with a binary label
    subjects = pd.DataFrame(
        {
            "subject_id": ["sub-01", "sub-02", "sub-03", "sub-04"],
            "decline_label": [0, 1, 0, 1],
        }
    )
    subjects_path = tmp_path / "eligible_subjects.csv"
    subjects.to_csv(subjects_path, index=False)

    # Create a matching graph metrics CSV with two dummy features
    metrics = pd.DataFrame(
        {
            "subject_id": ["sub-01", "sub-02", "sub-03", "sub-04"],
            "degree_mean": [0.5, 0.6, 0.55, 0.65],
            "efficiency": [0.8, 0.75, 0.78, 0.74],
        }
    )
    metrics_path = tmp_path / "graph_metrics.csv"
    metrics.to_csv(metrics_path, index=False)

    return subjects_path, metrics_path

def test_split_features_labels(tmp_path: Path):
    subjects_path, metrics_path = _create_dummy_data(tmp_path)

    X, y = evaluate.split_features_labels(metrics_path, subjects_path)

    # Expect four rows and two feature columns
    assert X.shape == (4, 2)
    assert np.array_equal(y, np.array([0, 1, 0, 1]))

def test_evaluate_model_runs(tmp_path: Path):
    subjects_path, metrics_path = _create_dummy_data(tmp_path)

    X, y = evaluate.split_features_labels(metrics_path, subjects_path)
    fold_metrics, mean_metrics = evaluate.evaluate_model(X, y, n_splits=2, random_state=0)

    # Two folds should be produced
    assert len(fold_metrics) == 2
    for fm in fold_metrics:
        assert "roc_auc" in fm and "accuracy" in fm and "f1" in fm

    # Mean metrics must contain the same keys
    assert set(mean_metrics.keys()) == {"roc_auc", "accuracy", "f1"}

def test_write_performance_report(tmp_path: Path):
    # Dummy metrics
    fold_metrics = [
        {"fold": 1, "roc_auc": 0.75, "accuracy": 0.8, "f1": 0.78},
        {"fold": 2, "roc_auc": 0.70, "accuracy": 0.75, "f1": 0.73},
    ]
    mean_metrics = {"roc_auc": 0.725, "accuracy": 0.775, "f1": 0.755}

    report_path = tmp_path / "performance_report.json"
    evaluate.write_performance_report(fold_metrics, mean_metrics, report_path)

    # Verify JSON structure
    with report_path.open() as f:
        data = json.load(f)

    assert "folds" in data and "mean" in data
    assert len(data["folds"]) == 2
    assert set(data["mean"].keys()) == {"roc_auc", "accuracy", "f1"}