"""
Unit tests for contract schema validation.
Ensures schemas are valid YAML and can be loaded by the schema generator.
"""
import pytest
import yaml
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.generate_schemas import load_schema

SCHEMAS_DIR = Path(__file__).parent.parent / "code" / "contracts"

def test_ceramic_entry_schema_loads():
    """Test that ceramic_entry.schema.yaml is valid YAML and loads correctly."""
    schema_path = SCHEMAS_DIR / "ceramic_entry.schema.yaml"
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    
    schema = load_schema(str(schema_path))
    
    # Verify required fields
    assert "title" in schema
    assert schema["title"] == "CeramicEntry"
    assert "properties" in schema
    assert "required" in schema
    
    # Verify specific required fields exist in schema
    required_fields = schema["required"]
    assert "composition" in required_fields
    assert "weibull_modulus" in required_fields
    assert "source_id" in required_fields

def test_model_result_schema_loads():
    """Test that model_result.schema.yaml is valid YAML and loads correctly."""
    schema_path = SCHEMAS_DIR / "model_result.schema.yaml"
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    
    schema = load_schema(str(schema_path))
    
    # Verify required fields
    assert "title" in schema
    assert schema["title"] == "ModelResult"
    assert "properties" in schema
    assert "required" in schema
    
    # Verify specific required fields
    required_fields = schema["required"]
    assert "model_type" in required_fields
    assert "metrics" in required_fields
    assert "timestamp" in required_fields

def test_schema_types_valid():
    """Verify that type definitions in schemas are valid JSON Schema types."""
    for schema_file in ["ceramic_entry.schema.yaml", "model_result.schema.yaml"]:
        schema_path = SCHEMAS_DIR / schema_file
        schema = load_schema(str(schema_path))
        
        def validate_node(node):
            if isinstance(node, dict):
                if "type" in node:
                    valid_types = ["string", "number", "integer", "boolean", "array", "object", "null"]
                    assert node["type"] in valid_types, f"Invalid type '{node['type']}' in {schema_file}"
                for value in node.values():
                    validate_node(value)
            elif isinstance(node, list):
                for item in node:
                    validate_node(item)
        
        validate_node(schema)