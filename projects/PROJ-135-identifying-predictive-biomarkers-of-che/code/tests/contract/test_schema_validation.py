"""
Contract test harness for YAML schema validation.
Validates that data artifacts conform to the schemas defined in specs/contracts.
"""
import os
import sys
import json
import yaml
from pathlib import Path
import pytest

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.config import get_project_root

# Schema paths relative to project root
SCHEMAS_DIR = "specs/001-chemo-biomarker-discovery/contracts"

# Define expected schemas based on T006
EXPECTED_SCHEMAS = [
    "dataset.schema.yaml",
    "model_output.schema.yaml",
    "meta_analysis.schema.yaml"
]

def load_schema(schema_name: str) -> dict:
    """Load a YAML schema definition from the contracts directory."""
    schema_path = get_project_root() / SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_type(value, expected_type, schema_name: str, field_path: str):
    """
    Basic type validation against schema definition.
    Supports: string, number, integer, boolean, array, object
    """
    if expected_type == "string":
        if not isinstance(value, str):
            raise TypeError(f"Field '{field_path}' expected string, got {type(value).__name__} in {schema_name}")
    elif expected_type in ["number", "integer"]:
        if not isinstance(value, (int, float)):
            raise TypeError(f"Field '{field_path}' expected number, got {type(value).__name__} in {schema_name}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            raise TypeError(f"Field '{field_path}' expected boolean, got {type(value).__name__} in {schema_name}")
    elif expected_type == "array":
        if not isinstance(value, list):
            raise TypeError(f"Field '{field_path}' expected array, got {type(value).__name__} in {schema_name}")
    elif expected_type == "object":
        if not isinstance(value, dict):
            raise TypeError(f"Field '{field_path}' expected object, got {type(value).__name__} in {schema_name}")

def validate_required_fields(data: dict, schema: dict, schema_name: str):
    """Validate that all required fields are present in the data."""
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    missing_fields = []
    for field in required:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields in {schema_name}: {missing_fields}")

def validate_data_against_schema(data: dict, schema: dict, schema_name: str, root_path: str = ""):
    """
    Recursively validate data against a JSON/YAML schema.
    This is a simplified validator suitable for contract testing.
    """
    properties = schema.get("properties", {})
    
    for field, value in data.items():
        field_path = f"{root_path}.{field}" if root_path else field
        
        if field not in properties:
            # Allow extra fields unless strict mode is defined (not in simple schema)
            continue
        
        field_schema = properties[field]
        field_type = field_schema.get("type")
        
        if field_type:
            validate_type(value, field_type, schema_name, field_path)
        
        # Recurse for objects
        if field_type == "object" and isinstance(value, dict):
            nested_schema = field_schema.get("properties", {})
            if nested_schema:
                # Create a pseudo-schema for the nested object
                nested_schema_wrapper = {"properties": nested_schema, "required": field_schema.get("required", [])}
                validate_data_against_schema(value, nested_schema_wrapper, schema_name, field_path)
        
        # Recurse for arrays of objects
        elif field_type == "array" and isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            items_schema = field_schema.get("items", {})
            if items_schema.get("type") == "object":
                item_schema_wrapper = {"properties": items_schema.get("properties", {}), "required": items_schema.get("required", [])}
                for idx, item in enumerate(value):
                    validate_data_against_schema(item, item_schema_wrapper, schema_name, f"{field_path}[{idx}]")

@pytest.mark.contract
def test_schemas_exist():
    """Verify that all expected schema files exist."""
    for schema_name in EXPECTED_SCHEMAS:
        schema_path = get_project_root() / SCHEMAS_DIR / schema_name
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

@pytest.mark.contract
def test_schemas_load_valid_yaml():
    """Verify that all schema files are valid YAML."""
    for schema_name in EXPECTED_SCHEMAS:
        try:
            schema = load_schema(schema_name)
            assert isinstance(schema, dict), f"Schema {schema_name} must be a dictionary"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {schema_name}: {e}")

@pytest.mark.contract
def test_dataset_schema_structure():
    """Validate the structure of the dataset schema."""
    schema = load_schema("dataset.schema.yaml")
    assert "properties" in schema
    assert "required" in schema
    # Check for expected top-level fields typically found in dataset schemas
    expected_fields = ["dataset_id", "source", "tumor_type", "sample_count"]
    for field in expected_fields:
        # Only assert if the field is defined in the schema's properties
        if field in schema.get("properties", {}):
            assert "type" in schema["properties"][field]

@pytest.mark.contract
def test_model_output_schema_structure():
    """Validate the structure of the model output schema."""
    schema = load_schema("model_output.schema.yaml")
    assert "properties" in schema
    assert "required" in schema

@pytest.mark.contract
def test_meta_analysis_schema_structure():
    """Validate the structure of the meta-analysis schema."""
    schema = load_schema("meta_analysis.schema.yaml")
    assert "properties" in schema
    assert "required" in schema

@pytest.mark.contract
def test_sample_data_validation():
    """
    Contract test: Validate a sample data artifact against its schema.
    This tests the validation logic itself.
    """
    # Create a mock dataset artifact that should pass validation
    mock_data = {
        "dataset_id": "TCGA-BRCA-001",
        "source": "TCGA",
        "tumor_type": "BRCA",
        "sample_count": 100,
        "features": ["GENE1", "GENE2"],
        "metadata": {
            "processed_date": "2023-10-01",
            "version": "1.0"
        }
    }
    
    schema = load_schema("dataset.schema.yaml")
    
    # Ensure required fields exist in mock data for the test to pass
    # This test assumes the schema defines 'dataset_id', 'source', etc. as required
    # If the schema is different, this test might need adjustment based on T006 output
    
    try:
        # Validate structure
        validate_required_fields(mock_data, schema, "dataset.schema.yaml")
        validate_data_against_schema(mock_data, schema, "dataset.schema.yaml")
    except (ValueError, TypeError, KeyError) as e:
        # If validation fails, it might be because the schema is more strict
        # or the mock data is incomplete. This is expected if schemas are complex.
        # We catch it to ensure the test harness itself works.
        # For a robust test, we ensure the mock data matches the schema exactly.
        # If the schema requires 'tumor_type' and 'sample_count', we have them.
        # If it requires something else, we might fail, which is a valid contract failure.
        pytest.fail(f"Mock data failed validation against dataset schema: {e}")

@pytest.mark.contract
def test_invalid_data_catches_error():
    """
    Contract test: Ensure the validator catches invalid data types.
    """
    mock_data = {
        "dataset_id": 12345,  # Should be string
        "source": "TCGA",
        "tumor_type": "BRCA",
        "sample_count": 100
    }
    
    schema = load_schema("dataset.schema.yaml")
    
    # We expect this to raise a TypeError if the schema defines dataset_id as string
    # and our validator is working.
    with pytest.raises(TypeError) as exc_info:
        validate_data_against_schema(mock_data, schema, "dataset.schema.yaml")
    
    assert "expected string" in str(exc_info.value).lower()
