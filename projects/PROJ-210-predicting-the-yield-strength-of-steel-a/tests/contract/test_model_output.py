"""
Contract tests for model output schema validation.

Validates that model evaluation artifacts conform to the schema defined
in contracts/output.schema.yaml.
"""

import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "output.schema.yaml"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the contracts directory."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: Any, schema_type: str) -> bool:
    """Validate a value against a JSON schema type."""
    if schema_type == "string":
        return isinstance(value, str)
    elif schema_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif schema_type == "boolean":
        return isinstance(value, bool)
    elif schema_type == "array":
        return isinstance(value, list)
    elif schema_type == "object":
        return isinstance(value, dict)
    elif schema_type == "null":
        return value is None
    return False

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> list:
    """
    Recursively validate data against a JSON schema.
    Returns a list of error messages.
    """
    errors = []
    
    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in data:
                errors.append(f"Missing required field: {path}.{field}")
    
    # Validate properties
    if "properties" in schema:
        for key, value in data.items():
            if key in schema["properties"]:
                prop_schema = schema["properties"][key]
                current_path = f"{path}.{key}" if path else key
                
                # Check type
                if "type" in prop_schema:
                    if not validate_type(value, prop_schema["type"]):
                        errors.append(f"Type mismatch at {current_path}: expected {prop_schema['type']}, got {type(value).__name__}")
                        continue
                
                # Check enum
                if "enum" in prop_schema:
                    if value not in prop_schema["enum"]:
                        errors.append(f"Invalid value at {current_path}: {value} not in {prop_schema['enum']}")
                
                # Check pattern (regex)
                if "pattern" in prop_schema and isinstance(value, str):
                    import re
                    if not re.match(prop_schema["pattern"], value):
                        errors.append(f"Pattern mismatch at {current_path}: {value} does not match {prop_schema['pattern']}")
                
                # Check minimum/maximum
                if "minimum" in prop_schema and isinstance(value, (int, float)):
                    if value < prop_schema["minimum"]:
                        errors.append(f"Value at {current_path} ({value}) is below minimum ({prop_schema['minimum']})")
                if "maximum" in prop_schema and isinstance(value, (int, float)):
                    if value > prop_schema["maximum"]:
                        errors.append(f"Value at {current_path} ({value}) is above maximum ({prop_schema['maximum']})")
                
                # Recurse for objects
                if prop_schema["type"] == "object" and isinstance(value, dict):
                    errors.extend(validate_against_schema(value, prop_schema, current_path))
                
                # Recurse for arrays
                if prop_schema["type"] == "array" and isinstance(value, list):
                    if "items" in prop_schema:
                        item_schema = prop_schema["items"]
                        for idx, item in enumerate(value):
                            if item_schema["type"] == "object" and isinstance(item, dict):
                                errors.extend(validate_against_schema(item, item_schema, f"{current_path}[{idx}]"))
                            elif "type" in item_schema:
                                if not validate_type(item, item_schema["type"]):
                                    errors.append(f"Array item type mismatch at {current_path}[{idx}]: expected {item_schema['type']}, got {type(item).__name__}")
                
                # Additional properties for metrics
                if prop_schema.get("additionalProperties") and isinstance(value, dict):
                    if isinstance(prop_schema["additionalProperties"], dict):
                        for sub_key, sub_val in value.items():
                            sub_schema = prop_schema["additionalProperties"]
                            sub_path = f"{current_path}.{sub_key}"
                            if "type" in sub_schema:
                                if not validate_type(sub_val, sub_schema["type"]):
                                    errors.append(f"Additional property type mismatch at {sub_path}: expected {sub_schema['type']}, got {type(sub_val).__name__}")
    
    return errors

@pytest.fixture
def schema():
    """Load the schema once for all tests."""
    return load_schema()

@pytest.fixture
def sample_model_output():
    """Generate a sample model output that should pass validation."""
    return {
        "model_name": "xgboost_yield_v1",
        "model_type": "XGBoost",
        "metrics": {
            "r2": 0.85,
            "rmse": 12.4,
            "mae": 9.8,
            "cv_scores": [0.82, 0.84, 0.86],
            "cv_mean": 0.84,
            "cv_std": 0.02
        },
        "feature_importance": [
            {"feature_name": "C", "importance_score": 0.25, "rank": 1},
            {"feature_name": "Mn", "importance_score": 0.18, "rank": 2},
            {"feature_name": "CoolingRate", "importance_score": 0.15, "rank": 3}
        ],
        "shap_summary": {
            "mean_abs_shap": {"C": 0.45, "Mn": 0.32, "CoolingRate": 0.28},
            "top_features": ["C", "Mn", "CoolingRate"],
            "plot_path": "data/results/shap_summary_plots/model_xgboost_shap_summary.png"
        },
        "permutation_test": {
            "interaction_terms": ["C_x_CoolingRate", "Cr_x_Ni"],
            "p_values": {"C_x_CoolingRate": 0.003, "Cr_x_Ni": 0.042},
            "is_significant": {"C_x_CoolingRate": True, "Cr_x_Ni": True},
            "fdr_corrected": True
        },
        "hyperparameters": {
            "max_depth": 6,
            "learning_rate": 0.1,
            "n_estimators": 100
        },
        "training_config": {
            "cv_folds": 3,
            "random_seed": 42,
            "cv_strategy": "KFold"
        },
        "timestamp": "2023-10-27T10:00:00Z",
        "data_checksum": "a" * 64,
        "version": "1.0.0"
    }

def test_schema_file_exists():
    """Test that the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Test that the schema file is valid YAML."""
    try:
        with open(SCHEMA_PATH, "r") as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema: {e}")

def test_model_output_schema_validation(schema, sample_model_output):
    """Test that a valid model output passes schema validation."""
    errors = validate_against_schema(sample_model_output, schema)
    assert len(errors) == 0, f"Schema validation failed: {errors}"

def test_missing_required_fields(schema):
    """Test that missing required fields are detected."""
    incomplete_output = {
        "model_name": "test_model",
        "model_type": "GAM"
        # Missing metrics, feature_importance, etc.
    }
    errors = validate_against_schema(incomplete_output, schema)
    assert len(errors) > 0
    assert any("Missing required field" in e for e in errors)

def test_invalid_model_type(schema):
    """Test that invalid model types are detected."""
    invalid_output = sample_model_output.copy()
    invalid_output["model_type"] = "InvalidModel"
    
    errors = validate_against_schema(invalid_output, schema)
    assert any("Invalid value at model_type" in e for e in errors)

def test_invalid_metric_range(schema):
    """Test that metrics outside valid ranges are detected."""
    invalid_output = sample_model_output.copy()
    invalid_output["metrics"]["r2"] = 1.5  # R2 cannot be > 1
    
    errors = validate_against_schema(invalid_output, schema)
    assert any("above maximum" in e for e in errors)

def test_invalid_plot_path_pattern(schema):
    """Test that invalid plot paths are detected."""
    invalid_output = sample_model_output.copy()
    invalid_output["shap_summary"]["plot_path"] = "invalid/path.txt"
    
    errors = validate_against_schema(invalid_output, schema)
    assert any("Pattern mismatch" in e for e in errors)

def test_checksum_format(schema):
    """Test that checksums must be valid SHA256 hex strings."""
    invalid_output = sample_model_output.copy()
    invalid_output["data_checksum"] = "not-a-valid-checksum"
    
    errors = validate_against_schema(invalid_output, schema)
    assert any("Pattern mismatch" in e for e in errors)

def test_p_values_range(schema):
    """Test that p-values must be between 0 and 1."""
    invalid_output = sample_model_output.copy()
    invalid_output["permutation_test"]["p_values"]["bad_term"] = 1.5
    
    errors = validate_against_schema(invalid_output, schema)
    assert any("above maximum" in e for e in errors)

def test_cv_scores_array(schema):
    """Test that cv_scores must be an array of numbers."""
    invalid_output = sample_model_output.copy()
    invalid_output["metrics"]["cv_scores"] = "not_an_array"
    
    errors = validate_against_schema(invalid_output, schema)
    assert any("Type mismatch at metrics.cv_scores" in e for e in errors)