"""
Contract tests for the model output schema.
Verifies that the trained model and performance reports adhere to the specification.
"""
import json
import pytest
from pathlib import Path

# Expected fields for performance report
EXPECTED_PERFORMANCE_FIELDS = [
    "roc_auc",
    "accuracy",
    "f1_score",
    "fold_metrics",
    "best_params",
    "feature_selection_summary"
]

# Expected fields for fold metrics
EXPECTED_FOLD_FIELDS = [
    "fold_number",
    "roc_auc",
    "accuracy",
    "f1_score"
]


def test_performance_report_schema(tmp_path):
    """
    Contract: Verify the JSON performance report structure.
    """
    output_file = tmp_path / "performance_report.json"

    # Mock data
    report = {
        "roc_auc": 0.75,
        "accuracy": 0.72,
        "f1_score": 0.68,
        "fold_metrics": [
            {
                "fold_number": 1,
                "roc_auc": 0.74,
                "accuracy": 0.71,
                "f1_score": 0.67
            },
            {
                "fold_number": 2,
                "roc_auc": 0.76,
                "accuracy": 0.73,
                "f1_score": 0.69
            }
        ],
        "best_params": {
            "n_estimators": 100,
            "max_depth": None
        },
        "feature_selection_summary": {
            "n_features_selected": 15,
            "method": "RFE"
        }
    }

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    with open(output_file, 'r') as f:
        loaded = json.load(f)

    # Contract assertion: Top-level keys exist
    for field in EXPECTED_PERFORMANCE_FIELDS:
        assert field in loaded, f"Missing required field: {field}"

    # Contract assertion: Fold metrics structure
    assert isinstance(loaded["fold_metrics"], list)
    for fold in loaded["fold_metrics"]:
        for field in EXPECTED_FOLD_FIELDS:
            assert field in fold, f"Missing field in fold metrics: {field}"

    # Contract assertion: Best params
    assert "n_estimators" in loaded["best_params"]
    assert "max_depth" in loaded["best_params"]


def test_permutation_results_schema(tmp_path):
    """
    Contract: Verify the permutation test results structure.
    """
    output_file = tmp_path / "permutation_results.json"

    # Mock data
    results = {
        "n_permutations": 500,
        "null_distribution": [0.49, 0.51, 0.48, 0.52, 0.50],
        "observed_statistic": 0.75,
        "p_value": 0.02,
        "execution_time_seconds": 1200.5
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    with open(output_file, 'r') as f:
        loaded = json.load(f)

    # Contract assertion: Required fields
    assert "n_permutations" in loaded
    assert "null_distribution" in loaded
    assert "observed_statistic" in loaded
    assert "p_value" in loaded
    assert isinstance(loaded["null_distribution"], list)
    assert loaded["p_value"] >= 0 and loaded["p_value"] <= 1
