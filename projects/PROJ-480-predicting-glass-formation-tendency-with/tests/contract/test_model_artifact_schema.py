"""
Contract test for the model artifact schema validation.
"""

import pytest
from jsonschema import validate, ValidationError
from tests.contract import load_schema

def test_model_artifact_schema_validity():
    """Test that the schema itself is valid JSON Schema."""
    schema = load_schema("model_artifact")
    assert isinstance(schema, dict)
    assert "properties" in schema

def test_model_artifact_schema_validation():
    """Test that valid model artifact passes schema validation."""
    schema = load_schema("model_artifact")
    valid_data = {
        "model_info": {
            "model_type": "XGBoostRegressor",
            "hyperparameters": {"max_depth": 3, "n_estimators": 100},
            "training_timestamp": "2023-10-27T10:00:00Z",
            "feature_columns": ["delta", "delta_h_mix", "delta_chi"],
            "target_type": "regression"
        },
        "performance_metrics": {
            "cv_score": 0.85,
            "cv_std": 0.02,
            "test_score": 0.84,
            "baseline_score": 0.5,
            "mdes": 0.1,
            "achieved_power": 0.9
        },
        "diagnostics": {
            "collinearity": {
                "vif_scores": {"delta": 2.5, "delta_h_mix": 3.0},
                "status": "OK",
                "comment": "No severe collinearity detected."
            },
            "circularity": {
                "linear_check": {
                    "r_squared": 0.5,
                    "passed": True
                },
                "permutation_check": {
                    "p_value": 0.01,
                    "passed": True
                },
                "comment": "Circularity checks passed."
            },
            "selection_bias": {
                "ks_statistic": 0.1,
                "passed": True,
                "comment": "No significant selection bias detected."
            }
        },
        "provenance": {
            "data_checksum": "abc123",
            "pipeline_version": "1.0.0"
        }
    }
    
    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_model_artifact_schema_collinearity_warning():
    """Test that collinearity warning status is valid."""
    schema = load_schema("model_artifact")
    valid_data = {
        "model_info": {
            "model_type": "Ridge",
            "hyperparameters": {"alpha": 1.0},
            "training_timestamp": "2023-10-27T10:00:00Z",
            "feature_columns": ["delta", "delta_h_mix"],
            "target_type": "regression"
        },
        "performance_metrics": {
            "cv_score": 0.7,
            "cv_std": 0.05
        },
        "diagnostics": {
            "collinearity": {
                "vif_scores": {"delta": 15.0},
                "status": "WARNING",
                "comment": "VIF > 10 detected, switched to Ridge."
            },
            "circularity": {
                "linear_check": {"r_squared": 0.5, "passed": True},
                "permutation_check": {"p_value": 0.01, "passed": True},
                "comment": "OK"
            },
            "selection_bias": {
                "ks_statistic": 0.1,
                "passed": True,
                "comment": "OK"
            }
        },
        "provenance": {
            "data_checksum": "abc123",
            "pipeline_version": "1.0.0"
        }
    }
    
    try:
        validate(instance=valid_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")