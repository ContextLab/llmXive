"""
Contract test for evaluation metrics output.

This test validates that the evaluation metrics produced by the modeling
pipeline exist and conform to a minimal schema. The expected file is
``data/model/evaluation_metrics.json`` and must contain the following
fields:

- ``roc_auc`` (float): ROC‑AUC score, must be in the range [0, 1].
- ``pr_auc`` (float): PR‑AUC score, must be in the range [0, 1].
- ``calibration_error`` (float): calibration error, non‑negative.
- ``thresholds_file`` (str, optional): path to the generated thresholds CSV.

The test is deliberately lightweight and does not depend on any
external libraries beyond the Python standard library and ``pytest``.
"""

import json
from pathlib import Path

import pytest

# Resolve the path to the evaluation metrics file relative to the repository root.
METRICS_PATH = (
    Path(__file__).resolve().parents[2]  # project root
    / "data"
    / "model"
    / "evaluation_metrics.json"
)

# Minimal required schema: field name -> expected Python type.
REQUIRED_FIELDS = {
    "roc_auc": float,
    "pr_auc": float,
    "calibration_error": float,
    # ``thresholds_file`` is optional for the strict schema check but,
    # if present, must be a string.
    "thresholds_file": (str, type(None)),
}


def _load_metrics() -> dict:
    """Load the JSON file containing evaluation metrics."""
    with METRICS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_evaluation_metrics_file_exists() -> None:
    """The evaluation metrics JSON file must exist."""
    assert METRICS_PATH.is_file(), f"Evaluation metrics file not found at {METRICS_PATH}"


def test_evaluation_metrics_schema() -> None:
    """Validate that the JSON file adheres to the required schema."""
    metrics = _load_metrics()

    # Check required fields and their types.
    for field, expected_type in REQUIRED_FIELDS.items():
        assert field in metrics, f"Missing required field '{field}' in evaluation metrics"

        # ``thresholds_file`` may be omitted; treat missing as ``None``.
        if field == "thresholds_file" and metrics[field] is None:
            continue

        assert isinstance(
            metrics[field], expected_type
        ), f"Field '{field}' should be of type {expected_type}"


    # Additional numeric sanity checks.
    roc_auc = metrics["roc_auc"]
    pr_auc = metrics["pr_auc"]
    calib_err = metrics["calibration_error"]

    assert 0.0 <= roc_auc <= 1.0, f"roc_auc out of bounds: {roc_auc}"
    assert 0.0 <= pr_auc <= 1.0, f"pr_auc out of bounds: {pr_auc}"
    assert calib_err >= 0.0, f"calibration_error must be non‑negative, got {calib_err}"

# The following test is optional but provides a quick sanity check that the
# thresholds file (if referenced) actually exists.
@pytest.mark.optionalhook
def test_thresholds_file_exists() -> None:
    """If a thresholds CSV is referenced, ensure the file exists."""
    metrics = _load_metrics()
    thresholds_path = metrics.get("thresholds_file")
    if thresholds_path:
        path = Path(thresholds_path)
        # Resolve relative to the repository root if the path is not absolute.
        if not path.is_absolute():
            path = METRICS_PATH.parent / path
        assert path.is_file(), f"Referenced thresholds file not found: {path}"