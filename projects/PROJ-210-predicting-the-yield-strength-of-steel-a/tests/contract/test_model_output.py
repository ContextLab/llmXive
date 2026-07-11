"""
Contract Test for Model Output Schema (T017)

Validates that model training outputs strictly adhere to the schema
defined in contracts/output.schema.yaml.

This test ensures:
1. All required fields are present.
2. Data types match the specification.
3. Enum values are valid.
4. Nested structures (metrics, feature_importance) are correct.
"""
import pytest
import json
import os
from datetime import datetime
from typing import Dict, Any
import yaml

# Path constants relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "contracts", "output.schema.yaml")

# Sample valid output data to test against the schema
# In a real integration scenario, this would be the actual output from src/models/train.py
SAMPLE_MODEL_OUTPUT = {
    "model_name": "xgboost_yield_strength_v1",
    "model_type": "XGBoost",
    "metrics": {
        "r2": 0.8542,
        "mse": 125.34,
        "rmse": 11.19,
        "mae": 8.45
    },
    "feature_importance": [
        {"feature": "Carbon_Content", "importance": 0.45},
        {"feature": "Manganese_Content", "importance": 0.22},
        {"feature": "Cooling_Rate_Holding_Time_Interact", "importance": 0.15},
        {"feature": "C_Cooling_Rate_Interact", "importance": 0.08}
    ],
    "interaction_p_values": [
        {"interaction_term": "Cooling_Rate_Holding_Time_Interact", "p_value": 0.003, "is_significant": True},
        {"interaction_term": "C_Cooling_Rate_Interact", "p_value": 0.042, "is_significant": True},
        {"interaction_term": "Cr_Ni_Ratio", "p_value": 0.15, "is_significant": False}
    ],
    "shap_summary_path": "data/results/shap_summary_plots/model_xgboost_shap_summary.png",
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

def load_schema() -> Dict[str, Any]:
    """Load the JSON/YAML schema from the contracts directory."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. Ensure T001/T017 created contracts/structure.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str) -> bool:
    """Helper to validate Python types against schema type strings."""
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float))
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return False

def validate_object(obj: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> list:
    """
    Recursive validator for the schema structure.
    Returns a list of error messages.
    """
    errors = []
    
    # Check required fields
    if "required" in schema:
        for field in schema["required"]:
            if field not in obj:
                errors.append(f"Missing required field: {path}.{field}")
    
    # Validate properties
    if "properties" in schema:
        for key, value in obj.items():
            if key in schema["properties"]:
                prop_schema = schema["properties"][key]
                prop_path = f"{path}.{key}" if path else key
                
                # Type check
                if "type" in prop_schema:
                    if not validate_type(value, prop_schema["type"]):
                        errors.append(f"Type mismatch at {prop_path}: expected {prop_schema['type']}, got {type(value).__name__}")
                    
                    # Enum check
                    if prop_schema["type"] == "string" and "enum" in prop_schema:
                        if value not in prop_schema["enum"]:
                            errors.append(f"Invalid enum value at {prop_path}: {value} not in {prop_schema['enum']}")
                    
                    # Nested object check
                    if prop_schema["type"] == "object":
                        errors.extend(validate_object(value, prop_schema, prop_path))
                    
                    # Array item check
                    if prop_schema["type"] == "array" and "items" in prop_schema:
                        if isinstance(value, list):
                            for i, item in enumerate(value):
                                item_path = f"{prop_path}[{i}]"
                                errors.extend(validate_object(item, prop_schema["items"], item_path))
            else:
                # Optional fields are allowed, but if we want to be strict about unknown fields:
                # errors.append(f"Unknown field at {path}.{key}")
                pass
    
    return errors

class TestModelOutputSchema:
    """Contract tests for model output validation."""

    def test_schema_file_exists(self):
        """Ensure the schema definition file exists."""
        assert os.path.exists(SCHEMA_PATH), "contracts/output.schema.yaml must exist"

    def test_schema_is_valid_yaml(self):
        """Ensure the schema file is valid YAML."""
        try:
            load_schema()
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in schema file: {e}")

    def test_sample_output_validates_against_schema(self):
        """
        Verify that a properly constructed model output object
        passes validation against the schema.
        """
        schema = load_schema()
        errors = validate_object(SAMPLE_MODEL_OUTPUT, schema)
        
        assert len(errors) == 0, f"Sample output failed schema validation:\n" + "\n".join(errors)

    def test_missing_required_field_fails(self):
        """Ensure validation catches missing required fields."""
        schema = load_schema()
        invalid_output = SAMPLE_MODEL_OUTPUT.copy()
        del invalid_output["model_name"]  # Remove required field
        
        errors = validate_object(invalid_output, schema)
        assert any("Missing required field" in err and "model_name" in err for err in errors), \
            "Validation should fail for missing 'model_name'"

    def test_invalid_enum_value_fails(self):
        """Ensure validation catches invalid model types."""
        schema = load_schema()
        invalid_output = SAMPLE_MODEL_OUTPUT.copy()
        invalid_output["model_type"] = "InvalidModelType"
        
        errors = validate_object(invalid_output, schema)
        assert any("Invalid enum value" in err for err in errors), \
            "Validation should fail for invalid 'model_type' enum"

    def test_wrong_data_type_fails(self):
        """Ensure validation catches type mismatches."""
        schema = load_schema()
        invalid_output = SAMPLE_MODEL_OUTPUT.copy()
        invalid_output["metrics"]["r2"] = "not_a_number"  # Should be number
        
        errors = validate_object(invalid_output, schema)
        assert any("Type mismatch" in err and "r2" in err for err in errors), \
            "Validation should fail for non-numeric 'r2'"

    def test_feature_importance_structure(self):
        """Ensure feature importance list items have correct structure."""
        schema = load_schema()
        invalid_output = SAMPLE_MODEL_OUTPUT.copy()
        invalid_output["feature_importance"] = [
            {"feature": "C", "importance": 0.5},
            {"importance": 0.2}  # Missing 'feature'
        ]
        
        errors = validate_object(invalid_output, schema)
        assert any("Missing required field" in err and "feature" in err for err in errors), \
            "Validation should fail for missing 'feature' in importance list"