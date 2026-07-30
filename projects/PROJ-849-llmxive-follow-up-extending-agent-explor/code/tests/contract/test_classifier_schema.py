"""
Contract tests for the classifier output schema.
Validates the structure of logistic regression classifier results.
"""
import pytest
from typing import Dict, Any, List


def validate_classifier_report(report: Dict[str, Any]) -> bool:
    """
    Validates a classifier analysis report.

    Expected schema:
    {
        "accuracy": float,
        "precision": float,
        "recall": float,
        "auc_roc": float,
        "threshold_met": bool,
        "model_path": str,
        "metrics_summary": str
    }
    """
    required_fields = {
        "accuracy": (int, float),
        "precision": (int, float),
        "recall": (int, float),
        "auc_roc": (int, float),
        "threshold_met": bool,
        "model_path": str,
        "metrics_summary": str
    }

    if not isinstance(report, dict):
        return False

    for field, expected_type in required_fields.items():
        if field not in report:
            return False
        if not isinstance(report[field], expected_type):
            return False

    return True


def test_classifier_output_schema() -> None:
    """Test that a valid classifier report passes validation."""
    valid_report = {
        "accuracy": 0.72,
        "precision": 0.70,
        "recall": 0.68,
        "auc_roc": 0.75,
        "threshold_met": True,
        "model_path": "models/logistic_regression.pkl",
        "metrics_summary": "Model exceeds 60% accuracy threshold."
    }
    assert validate_classifier_report(valid_report) is True


def test_classifier_output_threshold_not_met() -> None:
    """Test that a report with low accuracy is still valid structurally."""
    low_acc_report = {
        "accuracy": 0.45,
        "precision": 0.40,
        "recall": 0.38,
        "auc_roc": 0.52,
        "threshold_met": False,
        "model_path": "models/logistic_regression.pkl",
        "metrics_summary": "Model failed to meet 60% accuracy threshold."
    }
    assert validate_classifier_report(low_acc_report) is True