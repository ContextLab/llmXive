"""
Contract test for model output schema (T031).

Validates that the model training pipeline produces outputs adhering to the
expected schema defined in the project specifications. This includes:
1. Model artifacts (Pickle files) exist in results/models/.
2. Performance report (JSON) exists in results/reports/ and contains required fields.
3. Cross-system metrics (JSON) exist in results/reports/ if applicable.

This test assumes T033-T041 have been executed and produced the expected artifacts.
"""
import os
import json
import pytest
from pathlib import Path
from typing import Any, Dict

# Project root relative to test file
PROJECT_ROOT = Path(__file__).parent.parent.parent

REQUIRED_MODEL_FILES = [
    "random_forest.pkl",
    "gradient_boosting.pkl"
]

REQUIRED_REPORT_FIELDS = [
    "model_type",
    "accuracy",
    "auc_roc",
    "cross_validation_folds",
    "timestamp",
    "dataset_hash"
]

REQUIRED_CROSS_SYSTEM_FIELDS = [
    "train_family",
    "test_family",
    "accuracy",
    "auc_roc",
    "generalizability_flag"
]

MODEL_DIR = PROJECT_ROOT / "results" / "models"
REPORT_DIR = PROJECT_ROOT / "results" / "reports"

def test_model_artifacts_exist():
    """
    Contract: Model artifacts must exist in results/models/.
    Fails if T040 has not been run or files are missing.
    """
    assert MODEL_DIR.exists(), f"Model directory {MODEL_DIR} does not exist. Run T040."
    
    missing_files = []
    for file_name in REQUIRED_MODEL_FILES:
        file_path = MODEL_DIR / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    assert not missing_files, f"Missing model artifacts: {missing_files}. Ensure T040 has run."

def test_model_metrics_report_schema():
    """
    Contract: results/reports/model_metrics.json must exist and contain required fields.
    Validates the schema defined in T041.
    """
    report_path = REPORT_DIR / "model_metrics.json"
    assert report_path.exists(), f"Model metrics report {report_path} not found. Run T041."
    
    with open(report_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"model_metrics.json is not valid JSON: {e}")
    
    # Handle case where report might be a list of model results or a single dict
    models = data if isinstance(data, list) else [data]
    
    assert len(models) > 0, "model_metrics.json contains no model entries."
    
    for model_entry in models:
        missing_fields = []
        for field in REQUIRED_REPORT_FIELDS:
            if field not in model_entry:
                missing_fields.append(field)
        
        assert not missing_fields, (
            f"Model entry missing required schema fields: {missing_fields}. "
            f"Entry keys found: {list(model_entry.keys())}"
        )
        
        # Type checks for numeric fields
        for field in ["accuracy", "auc_roc"]:
            if field in model_entry:
                assert isinstance(model_entry[field], (int, float)), (
                    f"Field '{field}' must be numeric, got {type(model_entry[field])}"
                )

def test_cross_system_metrics_schema():
    """
    Contract: results/reports/cross_system_metrics.json must exist and contain required fields.
    Validates the schema defined in T039.
    """
    report_path = REPORT_DIR / "cross_system_metrics.json"
    
    # If T039 hasn't run or the file doesn't exist, this test fails explicitly
    if not report_path.exists():
        pytest.fail(
            f"Cross-system metrics report {report_path} not found. "
            "Ensure T039 has run to generate cross-system validation results."
        )
    
    with open(report_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"cross_system_metrics.json is not valid JSON: {e}")
    
    # Handle list or single dict
    entries = data if isinstance(data, list) else [data]
    
    assert len(entries) > 0, "cross_system_metrics.json contains no entries."
    
    for entry in entries:
        missing_fields = []
        for field in REQUIRED_CROSS_SYSTEM_FIELDS:
            if field not in entry:
                missing_fields.append(field)
        
        assert not missing_fields, (
            f"Cross-system entry missing required schema fields: {missing_fields}. "
            f"Entry keys found: {list(entry.keys())}"
        )
        
        # Validate generalizability flag if present
        if "generalizability_flag" in entry:
            assert entry["generalizability_flag"] in [True, False, "pending"], (
                f"generalizability_flag must be boolean or 'pending', got {entry['generalizability_flag']}"
            )