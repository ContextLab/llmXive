"""
Contract test framework implementation.

This module provides a reusable framework for validating JSON/YAML data artifacts
against the YAML schemas defined in specs/001-evaluating-the-explainability-of-llm-bas/contracts/.

It uses the `jsonschema` library to validate data instances.
"""
import json
import os
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Project root relative to this file (tests/contract)
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-evaluating-the-explainability-of-llm-bas" / "contracts"
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
EXPLANATIONS_DIR = PROJECT_ROOT / "explanations"

# Mapping of schema names to their file paths and expected data patterns
SCHEMA_REGISTRY = {
    "dataset": {
        "schema_file": "dataset.schema.yaml",
        "data_pattern": "data/**/*.json",
        "description": "Defects4J dataset records"
    },
    "patch": {
        "schema_file": "patch.schema.yaml",
        "data_pattern": "explanations/**/*_rationale.txt", # Patches are text, but we validate metadata if JSON
        "description": "Generated patch and rationale artifacts"
    },
    "correctness": {
        "schema_file": "correctness.schema.yaml",
        "data_pattern": "state/correctness.json",
        "description": "Correctness labels from test execution"
    },
    "explainability": {
        "schema_file": "explainability.schema.yaml",
        "data_pattern": "explanations/**/*_metadata.json",
        "description": "Explainability scores and metadata"
    },
    "statistical": {
        "schema_file": "statistical.schema.yaml",
        "data_pattern": "state/statistical_results.json",
        "description": "Statistical analysis results"
    }
}

def load_yaml_schema(schema_name: str) -> Dict[str, Any]:
    """
    Loads a YAML schema from the contracts directory.
    
    Args:
        schema_name: The key in SCHEMA_REGISTRY (e.g., 'dataset', 'patch').
        
    Returns:
        The parsed schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is invalid YAML.
    """
    schema_info = SCHEMA_REGISTRY.get(schema_name)
    if not schema_info:
        raise ValueError(f"Unknown schema name: {schema_name}")
        
    schema_path = SCHEMAS_DIR / schema_info["schema_file"]
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_data_instance(schema_name: str) -> List[Any]:
    """
    Loads data instances matching the pattern for a given schema.
    
    Args:
        schema_name: The key in SCHEMA_REGISTRY.
        
    Returns:
        A list of data instances (parsed JSON or YAML).
        
    Note:
        If no files match the pattern, returns an empty list.
        This allows tests to pass gracefully if data hasn't been generated yet,
        though in a full CI run, we might expect data to exist.
    """
    schema_info = SCHEMA_REGISTRY.get(schema_name)
    if not schema_info:
        raise ValueError(f"Unknown schema name: {schema_name}")
        
    pattern = schema_info["data_pattern"]
    # Determine base directory for globbing
    if pattern.startswith("data/"):
        base_dir = DATA_DIR
    elif pattern.startswith("state/"):
        base_dir = STATE_DIR
    elif pattern.startswith("explanations/"):
        base_dir = EXPLANATIONS_DIR
    else:
        base_dir = PROJECT_ROOT
        
    # Adjust pattern to be relative to base_dir
    relative_pattern = pattern.split("/", 1)[1] if "/" in pattern else pattern
    
    files = glob.glob(str(base_dir / relative_pattern), recursive=True)
    
    instances = []
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    continue
                # Try JSON first
                try:
                    data = json.loads(content)
                    instances.append(data)
                except json.JSONDecodeError:
                    # Try YAML
                    try:
                        data = yaml.safe_load(content)
                        instances.append(data)
                    except yaml.YAMLError:
                        # If it's a text file (like rationale), we skip JSON validation
                        # unless the schema expects a specific text format, which is rare for JSON schema.
                        # For now, we skip non-JSON/YAML files in this generic loader.
                        pass
        except Exception as e:
            # Log but don't fail the whole test suite on a single file read error
            print(f"Warning: Could not read {file_path}: {e}")
            
    return instances

def validate_instance_against_schema(instance: Any, schema: Dict[str, Any], schema_name: str, file_path: str = "unknown") -> bool:
    """
    Validates a single data instance against a schema.
    
    Args:
        instance: The data to validate.
        schema: The schema dictionary.
        schema_name: Name of the schema for error reporting.
        file_path: Source file path for error reporting.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If the instance does not match the schema.
    """
    try:
        # Use Draft7Validator for robust validation
        Draft7Validator.check_schema(schema)
        validate(instance=instance, schema=schema)
        return True
    except ValidationError as e:
        # Re-raise with more context
        raise ValidationError(
            f"Validation failed for {schema_name} in {file_path}: {e.message} "
            f"(Path: {list(e.path)})"
        )

# --- Pytest Tests ---

@pytest.mark.parametrize("schema_name", SCHEMA_REGISTRY.keys())
def test_schema_files_exist(schema_name: str):
    """Verify that all registered schema files exist on disk."""
    schema_info = SCHEMA_REGISTRY[schema_name]
    schema_path = SCHEMAS_DIR / schema_info["schema_file"]
    assert schema_path.exists(), f"Schema file missing: {schema_path}"

@pytest.mark.parametrize("schema_name", SCHEMA_REGISTRY.keys())
def test_schemas_are_valid_yaml(schema_name: str):
    """Verify that all schema files are valid YAML and parse correctly."""
    schema = load_yaml_schema(schema_name)
    assert isinstance(schema, dict), f"Schema {schema_name} must be a dictionary"
    assert "type" in schema or "$schema" in schema, f"Schema {schema_name} must have a 'type' or '$schema' definition"

@pytest.mark.parametrize("schema_name", SCHEMA_REGISTRY.keys())
def test_data_validates_against_schema(schema_name: str):
    """
    Validate all data instances found for a schema against its definition.
    
    If no data exists for a schema, this test is skipped (pytest.skip).
    """
    try:
        schema = load_yaml_schema(schema_name)
    except FileNotFoundError:
        pytest.skip(f"Schema not found for {schema_name}")
        
    instances = load_data_instance(schema_name)
    
    if not instances:
        pytest.skip(f"No data instances found for schema {schema_name} matching pattern {SCHEMA_REGISTRY[schema_name]['data_pattern']}")
        
    for i, instance in enumerate(instances):
        # Determine file path for error reporting (approximate)
        file_path = f"instance_{i}"
        
        # Validate
        validate_instance_against_schema(instance, schema, schema_name, file_path)

@pytest.mark.parametrize("schema_name", SCHEMA_REGISTRY.keys())
def test_schema_structure(schema_name: str):
    """
    Verify that the schema has the expected structure for a JSON Schema.
    """
    schema = load_yaml_schema(schema_name)
    
    # Basic checks
    assert isinstance(schema, dict)
    assert "$schema" in schema or "type" in schema, "Schema must define a type or $schema"
    
    # If it's an object schema, check properties
    if schema.get("type") == "object":
        assert "properties" in schema, "Object schema must have 'properties'"
        
    # If it's an array schema, check items
    if schema.get("type") == "array":
        assert "items" in schema, "Array schema must have 'items'"

# --- Integration Test for the Framework ---
def test_framework_loads_all_schemas_and_data():
    """
    A high-level integration test ensuring the framework can load all schemas
    and attempt to load data for each.
    """
    errors = []
    for name in SCHEMA_REGISTRY:
        try:
            load_yaml_schema(name)
            load_data_instance(name)
        except Exception as e:
            errors.append(f"{name}: {str(e)}")
    
    # We don't fail if data is missing, only if schemas are broken or logic errors occur
    # But we assert that no critical loading errors happened
    assert len(errors) == 0, f"Framework loading errors: {errors}"
