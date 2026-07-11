"""
Contract tests for the forgetting metric schema (US3).

Validates that the results produced by the analysis pipeline strictly adhere
to the expected JSON schema defined for forgetting metrics, ANOVA results,
and retention rates.
"""
import pytest
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

# Schema definitions for validation
FORGETTING_METRIC_SCHEMA = {
    "type": "object",
    "required": [
        "run_id",
        "condition",
        "initial_accuracy",
        "final_accuracy",
        "forgetting_rate",
        "retention_rates",
        "timestamp"
    ],
    "properties": {
        "run_id": {"type": "string"},
        "condition": {"type": "string", "enum": ["sequential", "mixed", "coevolving"]},
        "initial_accuracy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "final_accuracy": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "forgetting_rate": {"type": "number"},
        "retention_rates": {
            "type": "object",
            "additionalProperties": {"type": "number", "minimum": 0.0, "maximum": 1.0}
        },
        "timestamp": {"type": "string"}
    }
}

ANOVA_RESULT_SCHEMA = {
    "type": "object",
    "required": [
        "f_statistic",
        "p_value",
        "degrees_of_freedom",
        "effect_size",
        "post_hoc_tests"
    ],
    "properties": {
        "f_statistic": {"type": "number"},
        "p_value": {"type": "number"},
        "degrees_of_freedom": {
            "type": "object",
            "properties": {
                "between": {"type": "integer"},
                "within": {"type": "integer"}
            }
        },
        "effect_size": {"type": "number"},
        "post_hoc_tests": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "comparison": {"type": "string"},
                    "p_value": {"type": "number"},
                    "significant": {"type": "boolean"}
                }
            }
        }
    }
}

FULL_ANALYSIS_SCHEMA = {
    "type": "object",
    "required": [
        "metadata",
        "individual_runs",
        "anova_results",
        "retention_comparison"
    ],
    "properties": {
        "metadata": {
            "type": "object",
            "properties": {
                "total_runs": {"type": "integer"},
                "conditions": {"type": "array", "items": {"type": "string"}},
                "analysis_timestamp": {"type": "string"}
            }
        },
        "individual_runs": {
            "type": "array",
            "items": FORGETTING_METRIC_SCHEMA
        },
        "anova_results": ANOVA_RESULT_SCHEMA,
        "retention_comparison": {
            "type": "object",
            "properties": {
                "coevolving_mean_retention": {"type": "number"},
                "mixed_mean_retention": {"type": "number"},
                "difference": {"type": "number"},
                "statistically_significant": {"type": "boolean"}
            }
        }
    }
}

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Simple schema validator for the contract tests.
    Checks required fields and basic types.
    """
    errors = []
    
    # Check required keys
    for key in schema.get("required", []):
        if key not in data:
            errors.append(f"Missing required key: {key}")
    
    # Check properties
    for key, prop_schema in schema.get("properties", {}).items():
        if key not in data:
            continue
        
        value = data[key]
        expected_type = prop_schema.get("type")
        
        if expected_type == "object":
            if not isinstance(value, dict):
                errors.append(f"Key '{key}' must be an object")
            else:
                # Recursively validate nested object if it has its own schema
                if "properties" in prop_schema or "required" in prop_schema:
                    nested_errors = validate_schema(value, prop_schema)
                    errors.extend([f"{key}.{e}" for e in nested_errors])
        
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append(f"Key '{key}' must be an array")
            elif "items" in prop_schema:
                for i, item in enumerate(value):
                    item_errors = validate_schema(item, prop_schema["items"])
                    errors.extend([f"{key}[{i}].{e}" for e in item_errors])
        
        elif expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Key '{key}' must be a string")
            if "enum" in prop_schema and value not in prop_schema["enum"]:
                errors.append(f"Key '{key}' must be one of {prop_schema['enum']}")
        
        elif expected_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"Key '{key}' must be an integer")
        
        elif expected_type == "number":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"Key '{key}' must be a number")
            if "minimum" in prop_schema and value < prop_schema["minimum"]:
                errors.append(f"Key '{key}' value {value} is below minimum {prop_schema['minimum']}")
            if "maximum" in prop_schema and value > prop_schema["maximum"]:
                errors.append(f"Key '{key}' value {value} is above maximum {prop_schema['maximum']}")
        
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Key '{key}' must be a boolean")
    
    return errors

class TestForgettingMetricSchema:
    """Contract tests for the forgetting metric schema (T024)."""

    def test_valid_forgetting_metric(self):
        """Test a valid forgetting metric record."""
        valid_data = {
            "run_id": "run_001",
            "condition": "coevolving",
            "initial_accuracy": 0.95,
            "final_accuracy": 0.88,
            "forgetting_rate": 0.07,
            "retention_rates": {"rule_A": 0.92, "rule_B": 0.85},
            "timestamp": "2023-10-27T10:00:00Z"
        }
        errors = validate_schema(valid_data, FORGETTING_METRIC_SCHEMA)
        assert len(errors) == 0, f"Schema validation failed: {errors}"

    def test_invalid_condition_enum(self):
        """Test that invalid condition values are rejected."""
        invalid_data = {
            "run_id": "run_002",
            "condition": "invalid_condition",
            "initial_accuracy": 0.90,
            "final_accuracy": 0.85,
            "forgetting_rate": 0.05,
            "retention_rates": {},
            "timestamp": "2023-10-27T10:00:00Z"
        }
        errors = validate_schema(invalid_data, FORGETTING_METRIC_SCHEMA)
        assert any("condition" in e for e in errors), "Should reject invalid condition"

    def test_missing_required_field(self):
        """Test that missing required fields are detected."""
        invalid_data = {
            "run_id": "run_003",
            "condition": "sequential",
            # Missing initial_accuracy, final_accuracy, etc.
            "timestamp": "2023-10-27T10:00:00Z"
        }
        errors = validate_schema(invalid_data, FORGETTING_METRIC_SCHEMA)
        assert len(errors) > 0, "Should detect missing required fields"

    def test_accuracy_bounds(self):
        """Test that accuracy values are within [0.0, 1.0]."""
        invalid_data = {
            "run_id": "run_004",
            "condition": "mixed",
            "initial_accuracy": 1.5,
            "final_accuracy": 0.80,
            "forgetting_rate": -0.5,
            "retention_rates": {},
            "timestamp": "2023-10-27T10:00:00Z"
        }
        errors = validate_schema(invalid_data, FORGETTING_METRIC_SCHEMA)
        assert any("initial_accuracy" in e for e in errors), "Should reject accuracy > 1.0"
        assert any("forgetting_rate" in e for e in errors), "Should reject negative forgetting_rate if min is set"

    def test_valid_anova_result(self):
        """Test a valid ANOVA result structure."""
        valid_data = {
            "f_statistic": 4.56,
            "p_value": 0.012,
            "degrees_of_freedom": {"between": 2, "within": 87},
            "effect_size": 0.15,
            "post_hoc_tests": [
                {"comparison": "coevolving vs mixed", "p_value": 0.03, "significant": True},
                {"comparison": "sequential vs mixed", "p_value": 0.45, "significant": False}
            ]
        }
        errors = validate_schema(valid_data, ANOVA_RESULT_SCHEMA)
        assert len(errors) == 0, f"ANOVA schema validation failed: {errors}"

    def test_valid_full_analysis(self):
        """Test the complete analysis output schema."""
        valid_data = {
            "metadata": {
                "total_runs": 30,
                "conditions": ["sequential", "mixed", "coevolving"],
                "analysis_timestamp": "2023-10-27T11:00:00Z"
            },
            "individual_runs": [
                {
                    "run_id": "run_001",
                    "condition": "coevolving",
                    "initial_accuracy": 0.95,
                    "final_accuracy": 0.88,
                    "forgetting_rate": 0.07,
                    "retention_rates": {"rule_A": 0.92},
                    "timestamp": "2023-10-27T10:00:00Z"
                }
            ],
            "anova_results": {
                "f_statistic": 4.56,
                "p_value": 0.012,
                "degrees_of_freedom": {"between": 2, "within": 87},
                "effect_size": 0.15,
                "post_hoc_tests": [
                    {"comparison": "coevolving vs mixed", "p_value": 0.03, "significant": True}
                ]
            },
            "retention_comparison": {
                "coevolving_mean_retention": 0.88,
                "mixed_mean_retention": 0.75,
                "difference": 0.13,
                "statistically_significant": True
            }
        }
        errors = validate_schema(valid_data, FULL_ANALYSIS_SCHEMA)
        assert len(errors) == 0, f"Full analysis schema validation failed: {errors}"

    def test_missing_anova_in_full_analysis(self):
        """Test that missing anova_results in full analysis is caught."""
        invalid_data = {
            "metadata": {"total_runs": 30, "conditions": [], "analysis_timestamp": "now"},
            "individual_runs": [],
            "anova_results": None, # Should be object
            "retention_comparison": {}
        }
        errors = validate_schema(invalid_data, FULL_ANALYSIS_SCHEMA)
        assert any("anova_results" in e for e in errors), "Should detect invalid anova_results"