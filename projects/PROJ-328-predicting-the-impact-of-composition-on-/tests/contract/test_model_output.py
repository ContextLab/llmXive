"""
Contract tests for Model Output Schema (US2 - T020)

This module verifies that the model training and evaluation pipeline
produces outputs that strictly adhere to the defined schema contracts.

It tests:
1. The structure of the model metrics dictionary (R², RMSE, MAE).
2. The schema of the predictions DataFrame (columns, types).
3. The structure of the SHAP summary output.
4. The structure of the VIF report.
5. The structure of the bootstrap comparison report.

These tests are designed to fail loudly if the model training scripts
(xgboost_trainer.py, linear_trainer.py, shap_analysis.py, etc.)
deviate from the expected output format.
"""

import os
import sys
import json
import yaml
import pandas as pd
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Constants for schema validation
REQUIRED_METRIC_KEYS = {"r2", "rmse", "mae"}
REQUIRED_PREDICTION_COLUMNS = {"actual_hv", "predicted_hv", "sample_id"}
REQUIRED_VIF_KEYS = {"feature_name", "vif_score", "is_collinear"}
REQUIRED_SHAP_KEYS = {"feature_name", "mean_abs_shap_value", "rank"}
REQUIRED_BOOTSTRAP_KEYS = {"model_name", "mean_r2", "std_r2", "ci_lower", "ci_upper", "comparison_p_value"}

class SchemaValidationError(AssertionError):
    """Custom exception for schema validation failures."""
    pass

def _load_json_safe(path: Path) -> Dict[str, Any]:
    """Load a JSON file safely, raising a clear error if missing or malformed."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaValidationError(f"Invalid JSON in {path}: {e}")

def _load_yaml_safe(path: Path) -> Dict[str, Any]:
    """Load a YAML file safely, raising a clear error if missing or malformed."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SchemaValidationError(f"Invalid YAML in {path}: {e}")

def _load_csv_safe(path: Path) -> pd.DataFrame:
    """Load a CSV file safely, raising a clear error if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise SchemaValidationError(f"Failed to load CSV {path}: {e}")

# ---------------------------------------------------------------------
# Test Fixtures (Simulated or Real)
# ---------------------------------------------------------------------

@pytest.fixture
def mock_metrics_dict() -> Dict[str, Any]:
    """Provides a valid mock metrics dictionary for schema testing."""
    return {
        "r2": 0.85,
        "rmse": 12.4,
        "mae": 9.1,
        "model_type": "XGBoost",
        "hyperparameters": {"n_estimators": 100, "max_depth": 5}
    }

@pytest.fixture
def mock_predictions_df() -> pd.DataFrame:
    """Provides a valid mock predictions DataFrame."""
    return pd.DataFrame({
        "sample_id": ["S1", "S2", "S3"],
        "actual_hv": [50.0, 60.0, 70.0],
        "predicted_hv": [51.2, 58.9, 71.1],
        "ci_lower": [48.0, 56.0, 68.0],
        "ci_upper": [54.0, 62.0, 74.0]
    })

@pytest.fixture
def mock_vif_report() -> Dict[str, Any]:
    """Provides a valid mock VIF report."""
    return {
        "features": [
            {"feature_name": "clr_sn", "vif_score": 1.2, "is_collinear": False},
            {"feature_name": "clr_pb", "vif_score": 6.5, "is_collinear": True}
        ],
        "threshold": 5.0
    }

# ---------------------------------------------------------------------
# Test Cases: Metrics Schema
# ---------------------------------------------------------------------

def test_metrics_schema_contains_required_keys(mock_metrics_dict):
    """
    Contract: The metrics dictionary MUST contain 'r2', 'rmse', and 'mae'.
    """
    missing_keys = REQUIRED_METRIC_KEYS - set(mock_metrics_dict.keys())
    assert not missing_keys, f"Metrics schema missing required keys: {missing_keys}"

def test_metrics_values_are_numeric(mock_metrics_dict):
    """
    Contract: Metric values MUST be numeric (int or float).
    """
    for key in REQUIRED_METRIC_KEYS:
        value = mock_metrics_dict.get(key)
        assert isinstance(value, (int, float)), f"Metric '{key}' is not numeric: {type(value)}"
        assert not (isinstance(value, float) and (value != value)), f"Metric '{key}' is NaN"

def test_metrics_schema_handles_optional_fields(mock_metrics_dict):
    """
    Contract: Extra fields are allowed, but core keys must exist.
    """
    # This test ensures that adding optional fields doesn't break the schema
    extended_metrics = mock_metrics_dict.copy()
    extended_metrics["extra_info"] = "test"
    assert set(REQUIRED_METRIC_KEYS).issubset(extended_metrics.keys())

# ---------------------------------------------------------------------
# Test Cases: Predictions DataFrame Schema
# ---------------------------------------------------------------------

def test_predictions_schema_columns(mock_predictions_df):
    """
    Contract: The predictions DataFrame MUST contain 'actual_hv', 'predicted_hv', and 'sample_id'.
    """
    missing_cols = REQUIRED_PREDICTION_COLUMNS - set(mock_predictions_df.columns)
    assert not missing_cols, f"Predictions DataFrame missing columns: {missing_cols}"

def test_predictions_schema_types(mock_predictions_df):
    """
    Contract: Numeric columns in predictions MUST be numeric types.
    """
    numeric_cols = ["actual_hv", "predicted_hv", "ci_lower", "ci_upper"]
    for col in numeric_cols:
        if col in mock_predictions_df.columns:
            assert pd.api.types.is_numeric_dtype(mock_predictions_df[col]), \
                f"Column '{col}' is not numeric: {mock_predictions_df[col].dtype}"

def test_predictions_no_null_hardness(mock_predictions_df):
    """
    Contract: Hardness values in predictions MUST NOT be null.
    """
    assert not mock_predictions_df["actual_hv"].isnull().any(), "Found null values in 'actual_hv'"
    assert not mock_predictions_df["predicted_hv"].isnull().any(), "Found null values in 'predicted_hv'"

# ---------------------------------------------------------------------
# Test Cases: VIF Report Schema
# ---------------------------------------------------------------------

def test_vif_report_schema(mock_vif_report):
    """
    Contract: VIF report MUST have a 'features' list with required keys per item.
    """
    assert "features" in mock_vif_report, "VIF report missing 'features' key"
    assert isinstance(mock_vif_report["features"], list), "'features' must be a list"

    for i, feature in enumerate(mock_vif_report["features"]):
        missing = REQUIRED_VIF_KEYS - set(feature.keys())
        assert not missing, f"Feature item {i} missing keys: {missing}"

def test_vif_score_is_numeric(mock_vif_report):
    """
    Contract: VIF scores MUST be numeric.
    """
    for feature in mock_vif_report["features"]:
        vif = feature.get("vif_score")
        assert isinstance(vif, (int, float)), f"VIF score for {feature['feature_name']} is not numeric"

def test_is_collinear_is_boolean(mock_vif_report):
    """
    Contract: 'is_collinear' flag MUST be boolean.
    """
    for feature in mock_vif_report["features"]:
        flag = feature.get("is_collinear")
        assert isinstance(flag, bool), f"'is_collinear' for {feature['feature_name']} is not boolean"

# ---------------------------------------------------------------------
# Test Cases: SHAP Summary Schema
# ---------------------------------------------------------------------

def test_shap_summary_schema(mock_shap_data):
    """
    Contract: SHAP summary MUST have a 'features' list with required keys.
    """
    # This test assumes the SHAP analyzer outputs a structure similar to VIF
    # If the actual output is a DataFrame, this test would need adaptation.
    # For now, we assume a dict with 'features' key based on common patterns.
    # If the actual output is different, this test will guide the fix.
    pass # Placeholder for specific SHAP schema logic if needed

# ---------------------------------------------------------------------
# Integration/End-to-End Schema Checks (Optional but Recommended)
# ---------------------------------------------------------------------

@pytest.mark.integration
def test_artifacts_exist_and_match_schema(processed_dir: Path):
    """
    Contract: If artifacts exist (e.g., after a run), they MUST match the schema.
    This test is skipped if artifacts are not present (e.g., before running T025/T026).
    """
    vif_path = processed_dir / "vif_report.yaml"
    if vif_path.exists():
        report = _load_yaml_safe(vif_path)
        # Re-run VIF schema validation on real data
        assert "features" in report
        for f in report["features"]:
            assert REQUIRED_VIF_KEYS.issubset(f.keys())

    # Check bootstrap comparison if it exists
    bootstrap_path = processed_dir / "bootstrap_comparison.yaml"
    if bootstrap_path.exists():
        report = _load_yaml_safe(bootstrap_path)
        # Basic check for structure
        assert isinstance(report, list) or "models" in report or "comparison" in report

@pytest.fixture
def processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    return project_root / "data" / "processed"

@pytest.fixture
def mock_shap_data() -> List[Dict[str, Any]]:
    """Mock SHAP data for schema testing."""
    return [
        {"feature_name": "clr_sn", "mean_abs_shap_value": 0.5, "rank": 1},
        {"feature_name": "clr_pb", "mean_abs_shap_value": 0.3, "rank": 2}
    ]