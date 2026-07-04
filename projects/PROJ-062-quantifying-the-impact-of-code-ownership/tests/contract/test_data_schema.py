"""
Contract test for data schema validation.

Validates that the ownership and bug metadata schemas defined in
specs/001-code-ownership-analysis/contracts/ are correctly structured
and can be loaded/validated using PyYAML.

This test ensures:
1. Schema files exist and are valid YAML
2. Required fields are present in schemas
3. Data types and constraints are properly defined
4. Sample data can be validated against schemas
"""

import pytest
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List

# Project root is one level up from tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-code-ownership-analysis" / "contracts"

@pytest.fixture
def schema_dir() -> Path:
    """Return the contracts directory path."""
    assert CONTRACTS_DIR.exists(), f"Contracts directory not found: {CONTRACTS_DIR}"
    return CONTRACTS_DIR

@pytest.fixture
def ownership_schema(schema_dir: Path) -> Dict[str, Any]:
    """Load the ownership dataset schema."""
    schema_path = schema_dir / "dataset.schema.yaml"
    assert schema_path.exists(), f"Ownership schema not found: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema is not None, "Ownership schema is empty"
    assert "type" in schema, "Schema must define a type"
    assert schema["type"] == "object", "Dataset schema must be an object type"
    assert "properties" in schema, "Schema must define properties"
    return schema

@pytest.fixture
def output_schema(schema_dir: Path) -> Dict[str, Any]:
    """Load the output schema."""
    schema_path = schema_dir / "output.schema.yaml"
    assert schema_path.exists(), f"Output schema not found: {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert schema is not None, "Output schema is empty"
    return schema

def test_ownership_schema_has_required_fields(ownership_schema: Dict[str, Any]):
    """Test that ownership schema contains all required fields."""
    required_fields = ["repo_id", "module_path", "committer", "timestamp", "lines_added", "lines_deleted"]
    properties = ownership_schema.get("properties", {})
    
    for field in required_fields:
        assert field in properties, f"Required field '{field}' missing from ownership schema"

def test_ownership_schema_field_types(ownership_schema: Dict[str, Any]):
    """Test that ownership schema has correct field types."""
    properties = ownership_schema.get("properties", {})
    
    # repo_id should be string
    assert properties["repo_id"].get("type") == "string", "repo_id must be string"
    
    # module_path should be string
    assert properties["module_path"].get("type") == "string", "module_path must be string"
    
    # committer should be string
    assert properties["committer"].get("type") == "string", "committer must be string"
    
    # timestamp should be string (ISO format)
    assert properties["timestamp"].get("type") == "string", "timestamp must be string"
    
    # lines_added and lines_deleted should be integer
    assert properties["lines_added"].get("type") == "integer", "lines_added must be integer"
    assert properties["lines_deleted"].get("type") == "integer", "lines_deleted must be integer"

def test_ownership_schema_has_required_constraint(ownership_schema: Dict[str, Any]):
    """Test that ownership schema has required constraint list."""
    required = ownership_schema.get("required", [])
    assert "repo_id" in required, "repo_id must be required"
    assert "module_path" in required, "module_path must be required"
    assert "committer" in required, "committer must be required"
    assert "timestamp" in required, "timestamp must be required"

def test_output_schema_structure(output_schema: Dict[str, Any]):
    """Test that output schema has correct structure."""
    assert "type" in output_schema, "Output schema must define a type"
    assert output_schema["type"] == "object", "Output schema must be an object type"
    assert "properties" in output_schema, "Output schema must define properties"

def test_output_schema_contains_metrics(output_schema: Dict[str, Any]):
    """Test that output schema contains metric fields."""
    properties = output_schema.get("properties", {})
    
    # Check for key metric fields
    expected_fields = ["gini_coefficient", "code_churn", "cyclomatic_complexity", "bug_density"]
    for field in expected_fields:
        assert field in properties, f"Expected field '{field}' in output schema"

def test_sample_ownership_data_validates(ownership_schema: Dict[str, Any]):
    """Test that sample ownership data matches schema structure."""
    # Create sample data matching the schema
    sample_data = {
        "repo_id": "test-repo-001",
        "module_path": "src/main.py",
        "committer": "John Doe <john@example.com>",
        "timestamp": "2024-01-15T10:30:00Z",
        "lines_added": 150,
        "lines_deleted": 25
    }
    
    properties = ownership_schema.get("properties", {})
    
    # Validate each field exists and has correct type
    for field, value in sample_data.items():
        assert field in properties, f"Field '{field}' not in schema"
        
        expected_type = properties[field].get("type")
        if expected_type == "string":
            assert isinstance(value, str), f"{field} should be string"
        elif expected_type == "integer":
            assert isinstance(value, int), f"{field} should be integer"

def test_sample_output_data_validates(output_schema: Dict[str, Any]):
    """Test that sample output data matches schema structure."""
    sample_data = {
        "repo_id": "test-repo-001",
        "module_path": "src/main.py",
        "gini_coefficient": 0.45,
        "code_churn": 1250,
        "cyclomatic_complexity": 12,
        "bug_density": 2.5,
        "total_lines": 3500,
        "commit_count": 45
    }
    
    properties = output_schema.get("properties", {})
    
    for field, value in sample_data.items():
        assert field in properties, f"Field '{field}' not in output schema"

def test_schema_files_are_valid_yaml(schema_dir: Path):
    """Test that all schema files are valid YAML."""
    schema_files = list(schema_dir.glob("*.yaml"))
    assert len(schema_files) > 0, "No schema files found in contracts directory"
    
    for schema_file in schema_files:
        with open(schema_file, 'r') as f:
            try:
                content = yaml.safe_load(f)
                assert content is not None, f"Schema file {schema_file} is empty or invalid"
            except yaml.YAMLError as e:
                pytest.fail(f"Schema file {schema_file} is not valid YAML: {e}")

def test_ownership_schema_has_description(ownership_schema: Dict[str, Any]):
    """Test that ownership schema has a description."""
    assert "description" in ownership_schema, "Ownership schema must have a description"
    assert len(ownership_schema["description"]) > 0, "Ownership schema description cannot be empty"

def test_output_schema_has_description(output_schema: Dict[str, Any]):
    """Test that output schema has a description."""
    assert "description" in output_schema, "Output schema must have a description"
    assert len(output_schema["description"]) > 0, "Output schema description cannot be empty"

def test_ownership_schema_properties_have_descriptions(ownership_schema: Dict[str, Any]):
    """Test that ownership schema properties have descriptions."""
    properties = ownership_schema.get("properties", {})
    
    for field_name, field_def in properties.items():
        assert "description" in field_def, f"Property '{field_name}' must have a description"
        assert len(field_def["description"]) > 0, f"Property '{field_name}' description cannot be empty"

def test_schema_versioning(ownership_schema: Dict[str, Any], output_schema: Dict[str, Any]):
    """Test that schemas have version information."""
    # Check if version field exists (optional but recommended)
    if "version" in ownership_schema:
        assert isinstance(ownership_schema["version"], str), "Version should be a string"
    
    if "version" in output_schema:
        assert isinstance(output_schema["version"], str), "Version should be a string"