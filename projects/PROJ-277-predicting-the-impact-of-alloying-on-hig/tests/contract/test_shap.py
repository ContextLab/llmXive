"""
Contract test for SHAP report schema validation.

This test verifies that the SHAP analysis output artifacts (JSON report and PNG plot)
adhere to the expected schema defined in the project specifications.

It checks:
1. The existence of the output file (data/processed/shap_report.json).
2. The presence of required top-level keys: 'metadata', 'global_importance', 'sample_importance'.
3. The schema of 'global_importance' (list of dicts with 'feature', 'mean_abs_shap', 'rank').
4. The schema of 'metadata' (model_type, n_samples, timestamp).
5. The existence and non-empty size of the SHAP summary plot image (data/processed/shap_summary_plot.png).

This test is designed to fail if the schema changes or if the artifacts are missing,
ensuring strict contract compliance for User Story 3 (Interpretability).
"""
import os
import json
import pytest
from pathlib import Path

# Project root relative to test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
SHAP_REPORT_PATH = DATA_DIR / "shap_report.json"
SHAP_PLOT_PATH = DATA_DIR / "shap_summary_plot.png"

# Required schema definitions
REQUIRED_TOP_KEYS = {"metadata", "global_importance", "sample_importance"}
REQUIRED_METADATA_KEYS = {"model_type", "n_samples", "timestamp", "framing"}
REQUIRED_GLOBAL_IMP_KEYS = {"feature", "mean_abs_shap", "rank"}
REQUIRED_SAMPLE_IMP_KEYS = {"sample_id", "features", "predicted_value", "actual_value"}

def test_shap_report_file_exists():
    """Contract: The SHAP report JSON file must exist after pipeline execution."""
    assert SHAP_REPORT_PATH.exists(), f"SHAP report file not found at {SHAP_REPORT_PATH}"

def test_shap_plot_file_exists():
    """Contract: The SHAP summary plot image must exist after pipeline execution."""
    assert SHAP_PLOT_PATH.exists(), f"SHAP plot file not found at {SHAP_PLOT_PATH}"
    assert SHAP_PLOT_PATH.stat().st_size > 0, "SHAP plot file is empty"

def test_shap_report_schema_structure():
    """Contract: The SHAP report JSON must contain required top-level keys."""
    with open(SHAP_REPORT_PATH, "r") as f:
        report = json.load(f)

    missing_keys = REQUIRED_TOP_KEYS - set(report.keys())
    assert not missing_keys, f"SHAP report missing required top-level keys: {missing_keys}"

def test_shap_report_metadata_schema():
    """Contract: The 'metadata' section must contain required fields."""
    with open(SHAP_REPORT_PATH, "r") as f:
        report = json.load(f)

    metadata = report.get("metadata", {})
    missing_keys = REQUIRED_METADATA_KEYS - set(metadata.keys())
    assert not missing_keys, f"Metadata section missing required keys: {missing_keys}"

    # Validate specific metadata constraints
    assert metadata.get("framing") == "associational", "Metadata framing must be 'associational'"
    assert isinstance(metadata.get("n_samples"), int), "n_samples must be an integer"
    assert metadata.get("model_type") in ["RandomForest", "GradientBoosting", "GaussianProcess"], \
        "model_type must be one of the trained models"

def test_shap_report_global_importance_schema():
    """Contract: The 'global_importance' list must contain valid feature importance dicts."""
    with open(SHAP_REPORT_PATH, "r") as f:
        report = json.load(f)

    global_imp = report.get("global_importance", [])
    assert isinstance(global_imp, list), "global_importance must be a list"
    assert len(global_imp) > 0, "global_importance list cannot be empty"

    for idx, item in enumerate(global_imp):
        missing_keys = REQUIRED_GLOBAL_IMP_KEYS - set(item.keys())
        assert not missing_keys, f"Item {idx} in global_importance missing keys: {missing_keys}"
        
        # Type checks
        assert isinstance(item.get("feature"), str), f"Item {idx} 'feature' must be string"
        assert isinstance(item.get("mean_abs_shap"), (int, float)), f"Item {idx} 'mean_abs_shap' must be numeric"
        assert isinstance(item.get("rank"), int), f"Item {idx} 'rank' must be integer"
        
        # Rank consistency check (should be 1 to len(list))
        expected_rank = idx + 1
        assert item.get("rank") == expected_rank, \
            f"Item {idx} rank ({item.get('rank')}) does not match expected sorted order ({expected_rank})"

def test_shap_report_sample_importance_schema():
    """Contract: The 'sample_importance' list must contain valid sample explanation dicts."""
    with open(SHAP_REPORT_PATH, "r") as f:
        report = json.load(f)

    sample_imp = report.get("sample_importance", [])
    assert isinstance(sample_imp, list), "sample_importance must be a list"
    # Allow empty if no samples were processed, but if present, must be valid
    if len(sample_imp) > 0:
        for idx, item in enumerate(sample_imp):
            missing_keys = REQUIRED_SAMPLE_IMP_KEYS - set(item.keys())
            assert not missing_keys, f"Item {idx} in sample_importance missing keys: {missing_keys}"
            
            assert isinstance(item.get("sample_id"), (str, int)), f"Item {idx} 'sample_id' must be str or int"
            assert isinstance(item.get("features"), dict), f"Item {idx} 'features' must be a dict"
            assert isinstance(item.get("predicted_value"), (int, float)), f"Item {idx} 'predicted_value' must be numeric"
            assert isinstance(item.get("actual_value"), (int, float)), f"Item {idx} 'actual_value' must be numeric"

def test_shap_plot_content_type():
    """Contract: The SHAP plot must be a valid PNG image."""
    assert SHAP_PLOT_PATH.suffix.lower() == ".png", \
        f"SHAP plot must be a .png file, found {SHAP_PLOT_PATH.suffix}"
    
    # Check PNG magic bytes
    with open(SHAP_PLOT_PATH, "rb") as f:
        header = f.read(8)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", "File does not appear to be a valid PNG image"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])