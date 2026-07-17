"""
Contract tests for the analysis result schema (User Story 3).

This module verifies that the output of the logistic regression analysis
conforms to the expected schema structure defined in the project contracts.

The schema validates the structure of GLMMAnalysisResult objects which contain:
- Model fit statistics (AIC, BIC, log-likelihood)
- Coefficient estimates and standard errors
- P-values with significance flags
- AUC-ROC metrics
- Optimal threshold information
- Stratification details (if applicable)
"""

import json
import pytest
from pathlib import Path
import sys
from typing import Any, Dict

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.utils.validators import validate_json_schema, load_and_validate_jsonl

# Define the expected schema structure for analysis results
# This matches the structure expected by GLMMAnalysisResult and the final report
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AnalysisResultSchema",
    "description": "Schema for logistic regression analysis results",
    "type": "object",
    "required": [
        "model_fit",
        "coefficients",
        "p_values",
        "auc_roc",
        "optimal_threshold",
        "analysis_metadata"
    ],
    "properties": {
        "model_fit": {
            "type": "object",
            "required": ["log_likelihood", "aic", "bic"],
            "properties": {
                "log_likelihood": {"type": "number"},
                "aic": {"type": "number"},
                "bic": {"type": "number"},
                "n_obs": {"type": "integer", "minimum": 1},
                "n_params": {"type": "integer", "minimum": 1}
            }
        },
        "coefficients": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "estimate", "std_err", "z_stat"],
                "properties": {
                    "name": {"type": "string"},
                    "estimate": {"type": "number"},
                    "std_err": {"type": "number", "exclusiveMinimum": 0},
                    "z_stat": {"type": "number"},
                    "p_value": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "p_values": {
            "type": "object",
            "required": ["raw", "corrected", "significant"],
            "properties": {
                "raw": {
                    "type": "object",
                    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "corrected": {
                    "type": "object",
                    "description": "Bonferroni or Benjamini-Hochberg corrected p-values",
                    "additionalProperties": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "significant": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of coefficient names with p < 0.05 after correction"
                }
            }
        },
        "auc_roc": {
            "type": "object",
            "required": ["value", "confidence_interval"],
            "properties": {
                "value": {"type": "number", "minimum": 0, "maximum": 1},
                "confidence_interval": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "[lower_bound, upper_bound] for 95% CI"
                }
            }
        },
        "optimal_threshold": {
            "type": "object",
            "required": ["entropy_value", "method", "metrics"],
            "properties": {
                "entropy_value": {"type": "number"},
                "method": {"type": "string", "enum": ["min_weighted_error", "max_f1", "youden_j"]},
                "metrics": {
                    "type": "object",
                    "required": ["accuracy", "precision", "recall", "f1_score"],
                    "properties": {
                        "accuracy": {"type": "number", "minimum": 0, "maximum": 1},
                        "precision": {"type": "number", "minimum": 0, "maximum": 1},
                        "recall": {"type": "number", "minimum": 0, "maximum": 1},
                        "f1_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "false_positive_rate": {"type": "number", "minimum": 0, "maximum": 1},
                        "false_negative_rate": {"type": "number", "minimum": 0, "maximum": 1}
                    }
                }
            }
        },
        "stratification": {
            "type": ["object", "null"],
            "properties": {
                "method": {"type": "string", "enum": ["by_dataset", "by_layer_group", "continuous_covariate"]},
                "groups": {"type": "array", "items": {"type": "string"}},
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["group_name", "auc_roc", "significant"]
                    }
                }
            }
        },
        "analysis_metadata": {
            "type": "object",
            "required": ["dataset_used", "model_type", "timestamp"],
            "properties": {
                "dataset_used": {"type": "string"},
                "model_type": {"type": "string", "enum": ["GLMM", "LogisticRegression", "MixedEffects"]},
                "n_samples": {"type": "integer", "minimum": 1},
                "timestamp": {"type": "string", "format": "date-time"},
                "software_versions": {
                    "type": "object",
                    "properties": {
                        "python": {"type": "string"},
                        "statsmodels": {"type": "string"},
                        "numpy": {"type": "string"}
                    }
                }
            }
        }
    }
}


def test_schema_exists():
    """Verify that the schema definition exists and is valid JSON."""
    assert schema is not None
    assert isinstance(schema, dict)
    assert "$schema" in schema
    assert "properties" in schema


def test_schema_structure():
    """Verify the schema has all required top-level properties."""
    required_keys = [
        "model_fit", "coefficients", "p_values", 
        "auc_roc", "optimal_threshold", "analysis_metadata"
    ]
    for key in required_keys:
        assert key in schema["properties"], f"Missing required property: {key}"

def test_record_validation(tmp_path):
    """Test that a valid analysis result record passes schema validation."""
    # Create a valid sample record
    valid_record = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 0.00001
            },
            {
                "name": "intercept",
                "estimate": 1.2,
                "std_err": 0.15,
                "z_stat": 8.0,
                "p_value": 0.0
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001, "intercept": 0.0},
            "corrected": {"entropy": 0.00002, "intercept": 0.0},
            "significant": ["entropy", "intercept"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "analysis_metadata": {
            "dataset_used": "gsm8k_minigrid_combined",
            "model_type": "GLMM",
            "n_samples": 5000,
            "timestamp": "2024-01-15T10:30:00Z",
            "software_versions": {
                "python": "3.10.0",
                "statsmodels": "0.14.0",
                "numpy": "1.24.0"
            }
        }
    }
    
    # Write to a temporary file
    test_file = tmp_path / "valid_analysis_result.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(valid_record))
    
    # Validate against schema
    result = validate_json_schema(test_file, schema)
    assert result["valid"], f"Valid record failed schema validation: {result.get('errors')}"

def test_record_missing_field(tmp_path):
    """Test that a record with missing required fields fails validation."""
    invalid_record = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            # Missing 'bic'
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [],
        "p_values": {
            "raw": {},
            "corrected": {},
            "significant": []
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        # Missing 'optimal_threshold'
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "invalid_analysis_result.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(invalid_record))
    
    result = validate_json_schema(test_file, schema)
    assert not result["valid"], "Invalid record should fail schema validation"
    assert len(result.get("errors", [])) > 0, "Should report validation errors"

def test_record_wrong_type(tmp_path):
    """Test that a record with wrong data types fails validation."""
    invalid_record = {
        "model_fit": {
            "log_likelihood": "not_a_number",  # Wrong type
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 0.00001
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "wrong_type_analysis_result.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(invalid_record))
    
    result = validate_json_schema(test_file, schema)
    assert not result["valid"], "Record with wrong types should fail validation"

def test_coefficients_structure(tmp_path):
    """Test that coefficient array has correct structure."""
    invalid_record = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                # Missing 'estimate', 'std_err', 'z_stat'
                "p_value": 0.00001
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "invalid_coefficients.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(invalid_record))
    
    result = validate_json_schema(test_file, schema)
    assert not result["valid"], "Missing coefficient fields should fail validation"

def test_auc_roc_range(tmp_path):
    """Test that AUC-ROC values are within valid range [0, 1]."""
    invalid_record = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 0.00001
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 1.5,  # Out of range
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "invalid_auc_range.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(invalid_record))
    
    result = validate_json_schema(test_file, schema)
    assert not result["valid"], "AUC-ROC out of range should fail validation"

def test_optimal_threshold_method(tmp_path):
    """Test that optimal threshold method is one of the allowed values."""
    invalid_record = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 0.00001
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "invalid_method",  # Not in enum
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "invalid_threshold_method.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(invalid_record))
    
    result = validate_json_schema(test_file, schema)
    assert not result["valid"], "Invalid threshold method should fail validation"

def test_p_value_range(tmp_path):
    """Test that p-values are within valid range [0, 1]."""
    invalid_record = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 1.5  # Out of range
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "invalid_p_value_range.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(invalid_record))
    
    result = validate_json_schema(test_file, schema)
    assert not result["valid"], "P-value out of range should fail validation"

def test_stratification_optional(tmp_path):
    """Test that stratification is optional (can be null or missing)."""
    valid_record_no_strat = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 0.00001
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        # No stratification field
        "analysis_metadata": {
            "dataset_used": "test",
            "model_type": "GLMM",
            "n_samples": 100,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "no_stratification.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(valid_record_no_strat))
    
    result = validate_json_schema(test_file, schema)
    assert result["valid"], "Missing optional stratification should be valid"

def test_stratification_with_data(tmp_path):
    """Test that stratification with data validates correctly."""
    valid_record_with_strat = {
        "model_fit": {
            "log_likelihood": -1234.56,
            "aic": 2480.12,
            "bic": 2510.45,
            "n_obs": 5000,
            "n_params": 12
        },
        "coefficients": [
            {
                "name": "entropy",
                "estimate": -0.45,
                "std_err": 0.08,
                "z_stat": -5.625,
                "p_value": 0.00001
            }
        ],
        "p_values": {
            "raw": {"entropy": 0.00001},
            "corrected": {"entropy": 0.00002},
            "significant": ["entropy"]
        },
        "auc_roc": {
            "value": 0.85,
            "confidence_interval": [0.82, 0.88]
        },
        "optimal_threshold": {
            "entropy_value": 0.35,
            "method": "min_weighted_error",
            "metrics": {
                "accuracy": 0.82,
                "precision": 0.79,
                "recall": 0.85,
                "f1_score": 0.82,
                "false_positive_rate": 0.15,
                "false_negative_rate": 0.15
            }
        },
        "stratification": {
            "method": "by_dataset",
            "groups": ["gsm8k", "minigrid"],
            "results": [
                {
                    "group_name": "gsm8k",
                    "auc_roc": 0.88,
                    "significant": ["entropy"]
                },
                {
                    "group_name": "minigrid",
                    "auc_roc": 0.82,
                    "significant": ["entropy"]
                }
            ]
        },
        "analysis_metadata": {
            "dataset_used": "gsm8k_minigrid_combined",
            "model_type": "GLMM",
            "n_samples": 5000,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    
    test_file = tmp_path / "with_stratification.jsonl"
    with open(test_file, "w") as f:
        f.write(json.dumps(valid_record_with_strat))
    
    result = validate_json_schema(test_file, schema)
    assert result["valid"], "Valid stratification should pass validation"