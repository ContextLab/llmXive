"""
Contract test for SHAP output format (T028).

Verifies that SHAP analysis outputs conform to the expected schema defined
in contracts/model_output.schema.yaml (specifically the SHAP section) and
that the generated artifacts contain the required keys and data types.
"""
import os
import json
import pytest
from pathlib import Path
import yaml
import numpy as np
import pandas as pd

# Project root relative to test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_DIR = PROJECT_ROOT / "data"

# Expected output paths (based on standard pipeline execution)
EXPECTED_SUMMARY_JSON = DATA_DIR / "interpretation" / "shap_summary.json"
EXPECTED_FEATURE_IMP_JSON = DATA_DIR / "interpretation" / "feature_importance.json"
EXPECTED_SC002_MATCH = DATA_DIR / "validation" / "sc002_match_report.json"
EXPECTED_SC003_R2 = DATA_DIR / "validation" / "sc003_r2_report.json"

def load_schema():
    """Load the model output schema definition."""
    schema_path = CONTRACTS_DIR / "model_output.schema.yaml"
    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}. Foundation tasks may be incomplete.")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_shap_summary_json_schema_conformance():
    """
    Test that shap_summary.json exists and conforms to the schema.
    Required keys: model_name, timestamp, feature_names, shap_values (list of dicts),
    mean_abs_shap, top_features.
    """
    if not EXPECTED_SUMMARY_JSON.exists():
        # If the file doesn't exist, it might be because the pipeline hasn't run yet.
        # In a contract test, we check the format IF the file exists, or skip if
        # the pipeline phase isn't reached. However, for a robust test, we assert
        # existence if the model training phase (US2) is marked complete.
        # Given T028 is US3, we assume US2 (T026, T027) is done.
        # If the file is missing, we fail the contract test because the artifact
        # generation logic (T030/T032) is responsible for creating it.
        pytest.fail(f"SHAP summary output file not found: {EXPECTED_SUMMARY_JSON}. "
                    "The SHAP analysis pipeline (code/interpret/shap_analysis.py) must generate this file.")

    with open(EXPECTED_SUMMARY_JSON, 'r') as f:
        data = json.load(f)

    schema = load_schema()
    # Basic structural validation
    required_keys = ["model_name", "timestamp", "feature_names", "shap_values", "mean_abs_shap", "top_features"]
    for key in required_keys:
        assert key in data, f"Missing required key in SHAP summary: {key}"

    # Type validation
    assert isinstance(data["model_name"], str), "model_name must be a string"
    assert isinstance(data["timestamp"], str), "timestamp must be a string"
    assert isinstance(data["feature_names"], list), "feature_names must be a list"
    assert isinstance(data["shap_values"], list), "shap_values must be a list"
    assert isinstance(data["mean_abs_shap"], (list, dict)), "mean_abs_shap must be a list or dict"
    assert isinstance(data["top_features"], list), "top_features must be a list"

    # Validate top_features structure
    if data["top_features"]:
        first_feature = data["top_features"][0]
        assert "feature" in first_feature, "Top feature entry missing 'feature' key"
        assert "value" in first_feature, "Top feature entry missing 'value' key"

def test_feature_importance_json_schema_conformance():
    """
    Test that feature_importance.json exists and conforms to the schema.
    Required keys: model_name, feature_importances (list of dicts with feature, importance, p_value).
    """
    if not EXPECTED_FEATURE_IMP_JSON.exists():
        pytest.fail(f"Feature importance output file not found: {EXPECTED_FEATURE_IMP_JSON}. "
                    "The evaluation pipeline (code/models/evaluate.py) must generate this file.")

    with open(EXPECTED_FEATURE_IMP_JSON, 'r') as f:
        data = json.load(f)

    required_keys = ["model_name", "feature_importances"]
    for key in required_keys:
        assert key in data, f"Missing required key in feature importance: {key}"

    assert isinstance(data["feature_importances"], list), "feature_importances must be a list"
    
    if data["feature_importances"]:
        first_entry = data["feature_importances"][0]
        assert "feature" in first_entry, "Feature entry missing 'feature' key"
        assert "importance" in first_entry, "Feature entry missing 'importance' key"
        # P-value might be optional depending on the model, but if present, check type
        if "p_value" in first_entry:
            assert isinstance(first_entry["p_value"], (int, float)), "p_value must be numeric"

def test_sc002_match_report_format():
    """
    Test that sc002_match_report.json exists and has the correct structure.
    Required keys: consensus_list, top_features, matches, match_count, passed.
    """
    if not EXPECTED_SC002_MATCH.exists():
        # This file is only generated when external data is used.
        # If synthetic data is used, this file might not exist.
        # We skip if the file is missing to allow synthetic-only runs,
        # but if the file exists, it must be valid.
        pytest.skip(f"SC-002 report not found (expected only with external data): {EXPECTED_SC002_MATCH}")

    with open(EXPECTED_SC002_MATCH, 'r') as f:
        data = json.load(f)

    required_keys = ["consensus_list", "top_features", "matches", "match_count", "passed"]
    for key in required_keys:
        assert key in data, f"Missing required key in SC-002 report: {key}"

    assert isinstance(data["consensus_list"], list), "consensus_list must be a list"
    assert isinstance(data["top_features"], list), "top_features must be a list"
    assert isinstance(data["matches"], list), "matches must be a list"
    assert isinstance(data["match_count"], int), "match_count must be an integer"
    assert isinstance(data["passed"], bool), "passed must be a boolean"

    # Logic check: match_count should equal len(matches)
    assert data["match_count"] == len(data["matches"]), "match_count does not match len(matches)"

def test_sc003_r2_report_format():
    """
    Test that sc003_r2_report.json exists and has the correct structure.
    Required keys: model_type, features_used, r2_score, passed.
    """
    if not EXPECTED_SC003_R2.exists():
        pytest.skip(f"SC-003 report not found (expected only with external data): {EXPECTED_SC003_R2}")

    with open(EXPECTED_SC003_R2, 'r') as f:
        data = json.load(f)

    required_keys = ["model_type", "features_used", "r2_score", "passed"]
    for key in required_keys:
        assert key in data, f"Missing required key in SC-003 report: {key}"

    assert isinstance(data["model_type"], str), "model_type must be a string"
    assert isinstance(data["features_used"], list), "features_used must be a list"
    assert isinstance(data["r2_score"], (int, float)), "r2_score must be numeric"
    assert isinstance(data["passed"], bool), "passed must be a boolean"

    # Logic check: r2_score should be between -inf and 1.0 (typically)
    assert data["r2_score"] <= 1.0, "R2 score cannot be greater than 1.0"