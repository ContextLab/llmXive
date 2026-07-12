import pytest
import os
import yaml
import json
from code.data.loader import validate_fields, fetch_gatemem

def get_schema_path():
    """Locate the schema file relative to the project root."""
    # Try standard relative paths based on project structure
    # The task expects contracts/dataset.schema.yaml relative to root
    paths = [
        os.path.join("contracts", "dataset.schema.yaml"),
        os.path.join("..", "contracts", "dataset.schema.yaml"),
        os.path.join("..", "..", "contracts", "dataset.schema.yaml"),
        os.path.join("projects", "PROJ-830-llmxive-follow-up-extending-gatemem-benc", "contracts", "dataset.schema.yaml")
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("dataset.schema.yaml not found in expected paths")

def test_validate_fields_missing_required():
    """Test that validate_fields raises ValueError when required fields are missing."""
    schema_path = get_schema_path()
    
    # Load schema to know what is required
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    # Default to the known required fields if schema doesn't explicitly list them
    required = schema.get('required', ['outcome', 'predictors', 'covariates', 'leak-target'])
    
    # Create incomplete data
    incomplete_data = [
        {
            "outcome": "some_value",
            "predictors": "some_value",
            # Missing 'covariates' and 'leak-target'
        }
    ]
    
    with pytest.raises(ValueError) as exc_info:
        validate_fields(incomplete_data, schema_path)
    
    assert "Missing required field" in str(exc_info.value)
    for field in required:
        if field not in incomplete_data[0]:
            assert field in str(exc_info.value)

def test_validate_fields_success():
    """Test that validate_fields passes when all required fields are present."""
    schema_path = get_schema_path()
    
    # Load schema to know what is required
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    required = schema.get('required', ['outcome', 'predictors', 'covariates', 'leak-target'])
    
    # Create complete data
    complete_data = [
        {field: "dummy_value" for field in required}
    ]
    
    # Should not raise
    result = validate_fields(complete_data, schema_path)
    assert result == complete_data

def test_validate_fields_real_data():
    """Test validation against real fetched data (if available)."""
    schema_path = get_schema_path()
    try:
        data = fetch_gatemem()
        if not data:
            pytest.skip("No real data available for validation test")
        validate_fields(data, schema_path)
    except Exception as e:
        # If fetch fails (network, etc.), skip or fail based on environment
        # For robustness in CI, we might skip if data is not present
        if "Failed to load GateMem dataset" in str(e) or "Connection" in str(e):
            pytest.skip("GateMem dataset not accessible or network error")
        else:
            raise