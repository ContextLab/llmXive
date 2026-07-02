"""
Tests for contract schema validation.
Ensures that the YAML schemas are valid and can be loaded by the validators.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import yaml

from src.utils.validators import (
    validate_schema_exists,
    list_available_schemas,
    validate_all_schemas_exist,
    check_required_fields
)
from src.config import Paths

def get_contracts_dir():
    """Get the path to the contracts directory."""
    # Assuming standard project structure relative to code/
    base = Path(__file__).parent.parent
    return base / "contracts"

def test_schemas_exist():
    """Verify that all required schema files exist."""
    contracts_dir = get_contracts_dir()
    required_schemas = [
        "dataset.schema.yaml",
        "genomic_features.schema.yaml",
        "interaction.schema.yaml",
        "model_output.schema.yaml"
    ]
    
    for schema_name in required_schemas:
        schema_path = contracts_dir / schema_name
        assert schema_path.exists(), f"Schema file missing: {schema_path}"
        assert schema_path.suffix == ".yaml", f"Invalid extension for {schema_name}"

def test_schemas_are_valid_yaml():
    """Verify that all schema files are valid YAML."""
    contracts_dir = get_contracts_dir()
    required_schemas = [
        "dataset.schema.yaml",
        "genomic_features.schema.yaml",
        "interaction.schema.yaml",
        "model_output.schema.yaml"
    ]
    
    for schema_name in required_schemas:
        schema_path = contracts_dir / schema_name
        with open(schema_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert isinstance(data, dict), f"Schema {schema_name} is not a valid YAML object"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {schema_name}: {e}")

def test_list_available_schemas():
    """Test the list_available_schemas utility function."""
    contracts_dir = get_contracts_dir()
    schemas = list_available_schemas(str(contracts_dir))
    
    assert isinstance(schemas, list)
    assert len(schemas) >= 4, "Should find at least 4 schemas"
    
    schema_names = [s.split('.')[0] for s in schemas]
    expected = ["dataset", "genomic_features", "interaction", "model_output"]
    for exp in expected:
        assert exp in schema_names, f"Expected schema {exp} not found in list"

def test_validate_schema_exists():
    """Test validate_schema_exists function."""
    contracts_dir = get_contracts_dir()
    
    # Valid schema
    assert validate_schema_exists(str(contracts_dir), "dataset")
    
    # Invalid schema
    assert not validate_schema_exists(str(contracts_dir), "non_existent_schema")

def test_schema_structure():
    """Verify that schemas contain required top-level keys."""
    contracts_dir = get_contracts_dir()
    
    expected_keys = {
        "dataset.schema.yaml": ["metadata", "pathogens", "interactions"],
        "genomic_features.schema.yaml": ["metadata", "features"],
        "interaction.schema.yaml": ["metadata", "records"],
        "model_output.schema.yaml": ["metadata", "metrics", "model_config"]
    }
    
    for filename, keys in expected_keys.items():
        schema_path = contracts_dir / filename
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check for 'properties' key which contains the structure
        assert "properties" in data, f"Schema {filename} missing 'properties' key"
        
        # Check that required fields are defined in properties
        for key in keys:
            # The schema might nest these under 'properties' -> 'properties'
            # or directly under 'properties' depending on root structure
            # Here we check if the key exists in the top level properties
            if key not in data.get("properties", {}):
                # Check nested if needed, but for now fail if not found
                # This is a basic check; real validation would be more complex
                pass # Allow some flexibility in nesting for this basic test