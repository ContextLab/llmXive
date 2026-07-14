"""Unit tests for the training pipeline (task T023)."""

import json
from pathlib import Path

import pandas as pd
import pytest

# Import the public API we just implemented.
from code import (
    load_features,
    load_eligible_subjects,
    define_decline_label,
    make_inner_pipeline,
    train_and_evaluate_nested_cv,
    persist_model,
    write_performance_report,
)


@pytest.fixture
def dummy_features(tmp_path):
    """Create a minimal features CSV compatible with the pipeline."""
    df = pd.DataFrame(
        {
            "subject_id": [f"sub-{i:03d}" for i in range(10)],
            "feat_1": range(10),
            "feat_2": range(10, 20),
            "feat_3": range(20, 30),
        }
    )
    path = tmp_path / "graph_metrics.csv"
    df.to_csv(path, index=False)
    # Monkey‑patch the path used inside the module.
    Path("data/processed/graph_metrics.csv").parent.mkdir(parents=True, exist_ok=True)
    df.to_csv("data/processed/graph_metrics.csv", index=False)
    return df


@pytest.fixture
def dummy_eligible(tmp_path):
    """Create a minimal eligible subjects CSV with MMSE scores."""
    df = pd.DataFrame(
        {
            "subject_id": [f"sub-{i:03d}" for i in range(10)],
            "mmse_baseline": [30] * 10,
            "mmse_followup": [28, 30, 27, 30, 29, 30, 30, 30, 30, 30],
            "moca_baseline": [30] * 10,
            "moca_followup": [30] * 10,
        }
    )
    path = tmp_path / "eligible_subjects.csv"
    df.to_csv(path, index=False)
    Path("data/processed/eligible_subjects.csv").parent.mkdir(parents=True, exist_ok=True)
    df.to_csv("data/processed/eligible_subjects.csv", index=False)
    return df


def test_define_decline_label(dummy_eligible):
    df = define_decline_label(dummy_eligible)
    # Subjects with a ≥3‑point drop should have label 1.
    expected_labels = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    assert list(df["label"]) == expected_labels


def test_make_inner_pipeline():
    pipeline = make_inner_pipeline()
    # Ensure the pipeline has the expected steps.
    expected_steps = ["variance", "collinearity", "rfe", "clf"]
    assert [name for name, _ in pipeline.steps] == expected_steps


def test_full_training_flow(dummy_features, dummy_eligible):
    # Load data through the public helpers.
    X = load_features()
    eligible = load_eligible_subjects()

    # Merge manually the same way as main().
    merged = pd.merge(
        X,
        eligible,
        on="subject_id",
        how="inner",
        suffixes=("_feat", "_elig"),
    )
    merged = define_decline_label(merged)
    y = merged["label"]
    X_feat = merged.drop(columns=["label"])

    # Run nested CV (should succeed on tiny synthetic data).
    model, report = train_and_evaluate_nested_cv(X_feat, y)
    assert isinstance(report, dict)
    assert "mean_roc_auc" in report
    # Persist artefacts and verify they exist.
    persist_model(model)
    write_performance_report(report)
    assert Path("data/processed/model.pkl").is_file()
    assert Path("data/processed/performance_report.json").is_file()
    # Verify JSON content.
    with open("data/processed/performance_report.json") as f:
        loaded = json.load(f)
    assert loaded["mean_roc_auc"] == report["mean_roc_auc"]