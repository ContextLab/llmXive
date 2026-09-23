"""
Contract test for model output schema (US2).

This test validates that the model training and evaluation pipeline
produces outputs that strictly adhere to the defined schema contracts.
It does NOT train models itself; it validates the structure of artifacts
produced by the training tasks (T025, T026, T027, T029b, T030).

Run as: pytest tests/contract/test_model_output.py -v
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import get_data_processed_dir, get_data_outputs_dir, get_models_dir
from code.models.entities import SolderComposition, CompositionalDescriptor


# --- Schema Definitions (The Contract) ---

SCHEMA_CV_RESULTS = {
    "required_keys": [
        "model_name",
        "fold_number",
        "r2_score",
        "rmse",
        "mae",
        "fold_index"
    ],
    "type_checks": {
        "model_name": str,
        "fold_number": int,
        "r2_score": (int, float),
        "rmse": (int, float),
        "mae": (int, float),
        "fold_index": int
    }
}

SCHEMA_BOOTSTRAP_CIS = {
    "required_keys": [
        "r2_mean",
        "r2_ci_lower",
        "r2_ci_upper",
        "rmse_mean",
        "rmse_ci_lower",
        "rmse_ci_upper",
        "iterations"
    ],
    "type_checks": {
        "r2_mean": (int, float),
        "r2_ci_lower": (int, float),
        "r2_ci_upper": (int, float),
        "rmse_mean": (int, float),
        "rmse_ci_lower": (int, float),
        "rmse_ci_upper": (int, float),
        "iterations": int
    }
}

SCHEMA_VIF_REPORT = {
    "required_keys": [
        "features",
        "collinear_features",
        "threshold"
    ],
    "feature_schema": {
        "required_keys": ["feature_name", "vif_score", "is_collinear"],
        "type_checks": {
            "feature_name": str,
            "vif_score": (int, float),
            "is_collinear": bool
        }
    }
}

SCHEMA_SHAP_RANKING = {
    "required_keys": ["features"],
    "feature_schema": {
        "required_keys": ["feature_name", "mean_abs_shap_value", "rank"],
        "type_checks": {
            "feature_name": str,
            "mean_abs_shap_value": (int, float),
            "rank": int
        }
    }
}

SCHEMA_PREDICTIONS = {
    "required_columns": [
        "true_hardness_hv",
        "predicted_hardness_hv",
        "r2_ci_lower",
        "r2_ci_upper",
        "model_name"
    ],
    "type_checks": {
        "true_hardness_hv": (int, float),
        "predicted_hardness_hv": (int, float),
        "r2_ci_lower": (int, float),
        "r2_ci_upper": (int, float),
        "model_name": str
    }
}


class TestModelOutputContract:
    """Contract tests for model output artifacts."""

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        """Setup paths to expected artifacts."""
        self.processed_dir = get_data_processed_dir()
        self.models_dir = get_models_dir()
        self.outputs_dir = get_data_outputs_dir()

    def _validate_dict_schema(self, data: Dict[str, Any], schema: Dict, path_desc: str):
        """Helper to validate a dictionary against a schema."""
        errors = []
        
        # Check required keys
        for key in schema.get("required_keys", []):
            if key not in data:
                errors.append(f"Missing required key: '{key}' in {path_desc}")
        
        # Check types
        type_checks = schema.get("type_checks", {})
        for key, expected_type in type_checks.items():
            if key in data:
                if not isinstance(data[key], expected_type):
                    errors.append(
                        f"Type mismatch for '{key}' in {path_desc}: "
                        f"expected {expected_type}, got {type(data[key]).__name__}"
                    )
        
        return errors

    def test_cv_results_schema(self):
        """Validate cross-validation results JSON schema."""
        cv_path = self.processed_dir / "cv_results.json"
        
        if not cv_path.exists():
            pytest.skip(f"Artifact not found: {cv_path}. "
                      "Skipping contract test as training pipeline (T027) has not run yet.")
        
        with open(cv_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {cv_path}: {e}")
        
        if isinstance(data, list):
            # Validate each record in the list
            for i, record in enumerate(data):
                errors = self._validate_dict_schema(record, SCHEMA_CV_RESULTS, f"cv_results.json record {i}")
                assert not errors, f"Schema errors in cv_results.json record {i}: {errors}"
        elif isinstance(data, dict):
            # If it's a single record or nested structure, adapt check
            # Assuming it might be a dict of lists or similar, we check the first item if possible
            if "results" in data and isinstance(data["results"], list):
                for i, record in enumerate(data["results"]):
                    errors = self._validate_dict_schema(record, SCHEMA_CV_RESULTS, f"cv_results.json results[{i}]")
                    assert not errors, f"Schema errors in cv_results.json results[{i}]: {errors}"
            else:
                errors = self._validate_dict_schema(data, SCHEMA_CV_RESULTS, "cv_results.json (root)")
                assert not errors, f"Schema errors in cv_results.json: {errors}"

    def test_bootstrap_ci_schema(self):
        """Validate bootstrap confidence intervals YAML schema."""
        ci_path = self.processed_dir / "test_set_ci.yaml"
        
        if not ci_path.exists():
            pytest.skip(f"Artifact not found: {ci_path}. "
                      "Skipping contract test as bootstrap evaluation (T029b) has not run yet.")
        
        with open(ci_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {ci_path}: {e}")
        
        errors = self._validate_dict_schema(data, SCHEMA_BOOTSTRAP_CIS, "test_set_ci.yaml")
        assert not errors, f"Schema errors in test_set_ci.yaml: {errors}"

    def test_vif_report_schema(self):
        """Validate VIF report YAML schema."""
        vif_path = self.processed_dir / "vif_report.yaml"
        
        if not vif_path.exists():
            pytest.skip(f"Artifact not found: {vif_path}. "
                      "Skipping contract test as collinearity check (T054) has not run yet.")
        
        with open(vif_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {vif_path}: {e}")
        
        errors = self._validate_dict_schema(data, SCHEMA_VIF_REPORT, "vif_report.yaml")
        assert not errors, f"Schema errors in vif_report.yaml: {errors}"
        
        # Additional check for features list
        if "features" in data and isinstance(data["features"], list):
            for i, feat in enumerate(data["features"]):
                errors = self._validate_dict_schema(
                    feat, 
                    SCHEMA_VIF_REPORT["feature_schema"], 
                    f"vif_report.yaml features[{i}]"
                )
                assert not errors, f"Schema errors in vif_report.yaml features[{i}]: {errors}"

    def test_shap_ranking_schema(self):
        """Validate SHAP ranking YAML schema."""
        shap_path = self.processed_dir / "shap_ranking.yaml"
        
        if not shap_path.exists():
            pytest.skip(f"Artifact not found: {shap_path}. "
                      "Skipping contract test as SHAP analysis (T030) has not run yet.")
        
        with open(shap_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {shap_path}: {e}")
        
        errors = self._validate_dict_schema(data, SCHEMA_SHAP_RANKING, "shap_ranking.yaml")
        assert not errors, f"Schema errors in shap_ranking.yaml: {errors}"
        
        # Additional check for features list
        if "features" in data and isinstance(data["features"], list):
            for i, feat in enumerate(data["features"]):
                errors = self._validate_dict_schema(
                    feat, 
                    SCHEMA_SHAP_RANKING["feature_schema"], 
                    f"shap_ranking.yaml features[{i}]"
                )
                assert not errors, f"Schema errors in shap_ranking.yaml features[{i}]: {errors}"

    def test_predictions_schema(self):
        """Validate predictions CSV schema."""
        pred_path = self.processed_dir / "predictions.csv"
        
        if not pred_path.exists():
            pytest.skip(f"Artifact not found: {pred_path}. "
                      "Skipping contract test as inference (T031b) has not run yet.")
        
        import pandas as pd
        try:
            df = pd.read_csv(pred_path)
        except Exception as e:
            pytest.fail(f"Failed to read {pred_path}: {e}")
        
        # Check required columns
        missing_cols = set(SCHEMA_PREDICTIONS["required_columns"]) - set(df.columns)
        assert not missing_cols, f"Missing required columns in {pred_path}: {missing_cols}"
        
        # Check types for a sample of rows
        type_checks = SCHEMA_PREDICTIONS["type_checks"]
        sample_row = df.iloc[0].to_dict()
        
        for col, expected_type in type_checks.items():
            if col in sample_row:
                val = sample_row[col]
                if not isinstance(val, expected_type):
                    # Allow string representation of numbers if pandas reads them as objects sometimes, 
                    # but strictly check numeric types for contract
                    if not (isinstance(val, str) and val.replace('.', '', 1).isdigit()):
                        pytest.fail(
                            f"Type mismatch for column '{col}' in {pred_path}: "
                            f"expected {expected_type}, got {type(val).__name__} (value: {val})"
                        )