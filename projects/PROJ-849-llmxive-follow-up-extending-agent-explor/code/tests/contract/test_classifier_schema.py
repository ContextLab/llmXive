import pytest
from typing import Dict, Any, List

def validate_classifier_report(report: Dict[str, Any]) -> bool:
    """Validate the classifier report schema."""
    required_fields = ["accuracy", "precision", "recall", "auc_roc", "model_path"]
    
    for field in required_fields:
        if field not in report:
            return False
    
    if not isinstance(report["accuracy"], (int, float)):
        return False
    if not isinstance(report["precision"], (int, float)):
        return False
    if not isinstance(report["recall"], (int, float)):
        return False
    if not isinstance(report["auc_roc"], (int, float)):
        return False
    if not isinstance(report["model_path"], str):
        return False
        
    return True

def test_classifier_output_schema():
    """Test a valid classifier report."""
    sample = {
        "accuracy": 0.75,
        "precision": 0.70,
        "recall": 0.65,
        "auc_roc": 0.72,
        "model_path": "models/logistic_regression.pkl"
    }
    assert validate_classifier_report(sample) is True

def test_classifier_output_threshold_not_met():
    """Test that low accuracy is still valid schema-wise (threshold check is logic, not schema)."""
    sample = {
        "accuracy": 0.50,  # Below 60% threshold
        "precision": 0.45,
        "recall": 0.40,
        "auc_roc": 0.55,
        "model_path": "models/logistic_regression.pkl"
    }
    assert validate_classifier_report(sample) is True
