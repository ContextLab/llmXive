"""
Contract tests for Model Comparison Report Schema.
Verifies that the comparison report adheres to the expected schema.
"""
import pytest
from typing import Dict, Any

REQUIRED_KEYS = ["baseline_model", "salience_model", "improvement", "sensitivity_analysis"]
MODEL_KEYS = ["log_likelihood", "aic", "bic"]
IMPROVEMENT_KEYS = ["log_likelihood_diff", "aic_diff", "bic_diff", "p_value"]

def test_schema_structure(sample_comparison_report: Dict[str, Any]):
    """
    Contract Test: Verify report contains top-level required keys.
    """
    missing = set(REQUIRED_KEYS) - set(sample_comparison_report.keys())
    assert len(missing) == 0, f"Missing top-level keys: {missing}"

def test_schema_model_metrics(sample_comparison_report: Dict[str, Any]):
    """
    Contract Test: Verify both models contain log_likelihood, aic, bic.
    """
    for model_name in ["baseline_model", "salience_model"]:
        model_data = sample_comparison_report[model_name]
        missing = set(MODEL_KEYS) - set(model_data.keys())
        assert len(missing) == 0, f"Missing keys in {model_name}: {missing}"

def test_schema_improvement_metrics(sample_comparison_report: Dict[str, Any]):
    """
    Contract Test: Verify improvement section contains required metrics.
    """
    improvement = sample_comparison_report["improvement"]
    missing = set(IMPROVEMENT_KEYS) - set(improvement.keys())
    assert len(missing) == 0, f"Missing keys in improvement: {missing}"

def test_schema_sensitivity_analysis(sample_comparison_report: Dict[str, Any]):
    """
    Contract Test: Verify sensitivity analysis is a list of dicts with threshold, log_likelihood, aic.
    """
    sensitivity = sample_comparison_report["sensitivity_analysis"]
    assert isinstance(sensitivity, list), "sensitivity_analysis must be a list"
    assert len(sensitivity) > 0, "sensitivity_analysis cannot be empty"
    
    required_sens_keys = ["threshold", "log_likelihood", "aic"]
    for i, item in enumerate(sensitivity):
        missing = set(required_sens_keys) - set(item.keys())
        assert len(missing) == 0, f"Missing keys in sensitivity_analysis[{i}]: {missing}"

def test_schema_threshold_values(sample_comparison_report: Dict[str, Any]):
    """
    Contract Test: Verify specific threshold values {0.01, 0.05, 0.10} are present.
    """
    sensitivity = sample_comparison_report["sensitivity_analysis"]
    thresholds = {item["threshold"] for item in sensitivity}
    required_thresholds = {0.01, 0.05, 0.10}
    missing = required_thresholds - thresholds
    assert len(missing) == 0, f"Missing required threshold values: {missing}"
