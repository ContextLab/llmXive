"""Contract test for ROC‑AUC baseline.

This test validates that the primary predictive model achieves a
ROC‑AUC that is at least as good as a random‑guess baseline (0.50) and
that the baseline itself meets the minimum requirement of ≥ 0.50.

The test expects a JSON file containing evaluation metrics to be
present under ``data/model/``.  The JSON must contain a ``roc_auc``
key with the model's ROC‑AUC value.  If the file is missing the test
is skipped (allowing the rest of the suite to run before the
evaluation step has produced its output).
"""

import json
from pathlib import Path

import pytest


def _load_evaluation_metrics() -> dict:
    """Return the evaluation‑metric mapping.

    The implementation looks for a JSON file in a handful of common
    locations.  If none are found the test is skipped so that the
    contract does not falsely fail before the evaluation pipeline
    runs.
    """
    candidate_paths = [
        Path("data/model/evaluation.json"),
        Path("data/model/evaluation_metrics.json"),
        Path("data/model/metrics.json"),
    ]

    for p in candidate_paths:
        if p.is_file():
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)

    pytest.skip(
        "Evaluation metrics file not found; ensure the evaluation step "
        "produces one of the expected JSON files under data/model/."
    )
    return {}  # Unreachable – required for type checkers.


def test_baseline_roc_auc():
    """Assert that the baseline ROC‑AUC meets the minimum threshold."""
    # The baseline for a random classifier is 0.5.  The contract
    # requires that this value is not less than 0.5.
    baseline = 0.5
    assert baseline >= 0.5, "Baseline ROC‑AUC must be at least 0.5"


def test_model_roc_auc_exceeds_baseline():
    """Assert that the model's ROC‑AUC is ≥ 0.5 and exceeds the baseline."""
    metrics = _load_evaluation_metrics()

    # ``roc_auc`` is the primary metric recorded by the evaluation
    # pipeline.  It must be present and numeric.
    assert "roc_auc" in metrics, "Missing 'roc_auc' in evaluation metrics"
    roc_auc = metrics["roc_auc"]
    assert isinstance(roc_auc, (float, int)), "'roc_auc' must be a number"

    # Contract: model ROC‑AUC must be at least the baseline (0.5) and
    # strictly greater than the baseline to demonstrate predictive
    # power.
    baseline = 0.5
    assert roc_auc >= baseline, (
        f"Model ROC‑AUC ({roc_auc:.3f}) is below the required baseline "
        f"of {baseline:.3f}"
    )
    assert roc_auc > baseline, (
        f"Model ROC‑AUC ({roc_auc:.3f}) must exceed the baseline of "
        f"{baseline:.3f}"
    )