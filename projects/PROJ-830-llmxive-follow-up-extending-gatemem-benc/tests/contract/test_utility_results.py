import json
import os
import pytest
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary representation of the schema.
    """
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        pytest.skip("PyYAML not installed")
    except FileNotFoundError:
        pytest.fail(f"Schema file not found: {schema_path}")
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema file: {e}")

def validate_utility_results(result_path: str, schema_path: str) -> bool:
    """Validate utility results against the results schema.
    
    Args:
        result_path: Path to the utility results JSON file.
        schema_path: Path to the results schema YAML file.
        
    Returns:
        True if validation passes.
        
    Raises:
        AssertionError: If validation fails.
    """
    # Load schema
    schema = load_schema(schema_path)
    
    # Load results
    try:
        with open(result_path, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Results file not found: {result_path}")
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in results file: {e}")
    
    # Check required fields from schema
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    for field in required_fields:
        if field not in results:
            pytest.fail(f"Missing required field in results: {field}")
    
    # Specifically check for utility-related fields mentioned in task
    if 'conditional_utility' not in results:
        pytest.fail("Missing 'conditional_utility' field in utility results")
        
    if 'overall_success' not in results:
        pytest.fail("Missing 'overall_success' field in utility results")
    
    # Validate types if specified in schema
    for field, spec in properties.items():
        if field in results:
            expected_type = spec.get('type')
            if expected_type == 'number' and not isinstance(results[field], (int, float)):
                pytest.fail(f"Field '{field}' should be a number, got {type(results[field])}")
            elif expected_type == 'string' and not isinstance(results[field], str):
                pytest.fail(f"Field '{field}' should be a string, got {type(results[field])}")
            elif expected_type == 'array' and not isinstance(results[field], list):
                pytest.fail(f"Field '{field}' should be an array, got {type(results[field])}")
            elif expected_type == 'object' and not isinstance(results[field], dict):
                pytest.fail(f"Field '{field}' should be an object, got {type(results[field])}")
    
    return True

def test_utility_results_schema():
    """Contract test: Verify data/processed/utility_results.json contains required fields."""
    # Determine paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    results_path = project_root / "data" / "processed" / "utility_results.json"
    schema_path = project_root / "contracts" / "results.schema.yaml"
    
    # Skip if results file doesn't exist yet (e.g., during initial setup)
    if not results_path.exists():
        pytest.skip(f"Results file not yet generated: {results_path}")
        
    # Run validation
    validate_utility_results(str(results_path), str(schema_path))