"""
Contract test for modality_model schema (T013).

Validates that modality model configurations adhere to the schema defined
in contracts/modality_model.schema.yaml.

This test ensures:
1. The schema file exists and is valid YAML.
2. Sample configurations validate against the required fields:
   - model_id (string)
   - model_type (string)
   - max_memory_gb (number)
3. Invalid configurations are correctly rejected.
"""

import os
import pytest
import yaml
from pathlib import Path

# Import utilities from existing project structure if needed, 
# though this is a pure schema validation test.
# We rely on standard library and pytest.

CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "modality_model.schema.yaml"

# Sample valid configurations for testing
VALID_CONFIGS = [
    {
        "model_id": "timeseries_transformer_v1",
        "model_type": "TimeSeries-Transformer",
        "max_memory_gb": 0.8
    },
    {
        "model_id": "tabular_pfn_v2",
        "model_type": "TabPFN",
        "max_memory_gb": 0.5
    },
    {
        "model_id": "distilled_llm_text",
        "model_type": "DistilledLLM",
        "max_memory_gb": 0.9
    }
]

# Sample invalid configurations
INVALID_CONFIGS = [
    # Missing model_id
    {
        "model_type": "TimeSeries-Transformer",
        "max_memory_gb": 0.8
    },
    # Missing model_type
    {
        "model_id": "timeseries_transformer_v1",
        "max_memory_gb": 0.8
    },
    # Missing max_memory_gb
    {
        "model_id": "timeseries_transformer_v1",
        "model_type": "TimeSeries-Transformer"
    },
    # Wrong type for max_memory_gb (string instead of number)
    {
        "model_id": "timeseries_transformer_v1",
        "model_type": "TimeSeries-Transformer",
        "max_memory_gb": "0.8"
    },
    # Empty dict
    {}
]

def load_schema():
    """Load the modality_model schema contract."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_config_against_schema(config, schema):
    """
    Simple validation logic mimicking a JSON schema validator.
    Checks for required fields and basic type constraints.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Check types
    for field, value in config.items():
        if field in properties:
            expected_type = properties[field].get("type")
            if expected_type == "string":
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif expected_type == "number":
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be boolean, got {type(value).__name__}")
    
    return errors

class TestModalityModelSchema:
    """Contract tests for the modality_model schema."""

    def test_schema_file_exists(self):
        """Verify that the schema contract file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Verify that the schema file is valid YAML."""
        try:
            schema = load_schema()
            assert isinstance(schema, dict), "Schema root must be a dictionary"
            assert "required" in schema, "Schema must define 'required' fields"
            assert "properties" in schema, "Schema must define 'properties'"
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")
        except FileNotFoundError:
            pytest.fail("Schema file not found")

    def test_valid_configs_pass_validation(self):
        """Verify that valid configurations pass schema validation."""
        schema = load_schema()
        
        for i, config in enumerate(VALID_CONFIGS):
            errors = validate_config_against_schema(config, schema)
            assert len(errors) == 0, f"Valid config {i} failed validation: {errors}"

    def test_invalid_configs_fail_validation(self):
        """Verify that invalid configurations fail schema validation."""
        schema = load_schema()
        
        for i, config in enumerate(INVALID_CONFIGS):
            errors = validate_config_against_schema(config, schema)
            assert len(errors) > 0, f"Invalid config {i} should have failed but passed. Errors: {errors}"

    def test_schema_matches_contract_requirements(self):
        """
        Verify the schema contains the specific fields required by the contract.
        Contract (T013): model_id, model_type, max_memory_gb
        """
        schema = load_schema()
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        expected_fields = ["model_id", "model_type", "max_memory_gb"]
        
        for field in expected_fields:
            assert field in required_fields, f"Required field '{field}' missing from schema"
            assert field in properties, f"Property definition for '{field}' missing from schema"
        
        # Verify types
        assert properties.get("model_id", {}).get("type") == "string"
        assert properties.get("model_type", {}).get("type") == "string"
        assert properties.get("max_memory_gb", {}).get("type") == "number"