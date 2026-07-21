"""
Schema Validator for llmXive Project.

This module provides functionality to validate JSON output files against
their corresponding contract schemas defined in the contracts/ directory.

It is used for T036: Final verification of all JSON outputs against contract schemas.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON schema from a YAML file.
    
    Args:
        schema_path: Path to the schema file (.yaml or .json)
        
    Returns:
        The schema as a dictionary
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist
        ValueError: If the schema file is invalid
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            if schema_path.suffix in ['.yaml', '.yml']:
                schema = yaml.safe_load(f)
            else:
                schema = json.load(f)
        
        if not isinstance(schema, dict):
            raise ValueError(f"Invalid schema format in {schema_path}")
        
        return schema
    except Exception as e:
        raise ValueError(f"Failed to load schema from {schema_path}: {e}")


def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate JSON data against a schema using basic validation logic.
    
    This implements a simplified validator that checks:
    - Required fields
    - Field types (string, number, boolean, array, object)
    - Array item types
    - Nested object structures
    
    For full JSON Schema validation, jsonschema library would be used,
    but we implement a basic version to avoid additional dependencies.
    
    Args:
        data: The JSON data to validate
        schema: The schema to validate against
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    def validate_type(value: Any, expected_type: str, path: str) -> bool:
        """Validate that a value matches the expected type."""
        type_map = {
            'string': str,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        
        if expected_type not in type_map:
            errors.append(f"Unknown type '{expected_type}' at {path}")
            return False
        
        if not isinstance(value, type_map[expected_type]):
            errors.append(f"Expected {expected_type} at {path}, got {type(value).__name__}")
            return False
        
        return True
    
    def validate_object(obj: Dict[str, Any], schema_obj: Dict[str, Any], path: str = ""):
        """Validate an object against an object schema."""
        # Check required fields
        if 'required' in schema_obj:
            for field in schema_obj['required']:
                if field not in obj:
                    errors.append(f"Missing required field '{field}' at {path}")
        
        # Check properties
        if 'properties' in schema_obj:
            for prop_name, prop_schema in schema_obj['properties'].items():
                if prop_name in obj:
                    prop_path = f"{path}.{prop_name}" if path else prop_name
                    validate_value(obj[prop_name], prop_schema, prop_path)
    
    def validate_array(arr: List[Any], schema_arr: Dict[str, Any], path: str = ""):
        """Validate an array against an array schema."""
        if 'items' in schema_arr:
            item_schema = schema_arr['items']
            for i, item in enumerate(arr):
                item_path = f"{path}[{i}]"
                validate_value(item, item_schema, item_path)
    
    def validate_value(value: Any, schema_def: Dict[str, Any], path: str = ""):
        """Validate a value against a schema definition."""
        if 'type' in schema_def:
            if not validate_type(value, schema_def['type'], path):
                return
        
        if isinstance(value, dict) and schema_def.get('type') == 'object':
            validate_object(value, schema_def, path)
        elif isinstance(value, list) and schema_def.get('type') == 'array':
            validate_array(value, schema_def, path)
    
    validate_object(data, schema, "")
    return len(errors) == 0, errors


def validate_output_file(output_path: Path, schema_name: str, contracts_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate a single output file against its schema.
    
    Args:
        output_path: Path to the JSON output file
        schema_name: Name of the schema file (without extension)
        contracts_dir: Directory containing contract schemas
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # Load the data
    if not output_path.exists():
        return False, [f"Output file not found: {output_path}"]
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in {output_path}: {e}"]
    
    # Load the schema
    schema_path = contracts_dir / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        # Try .json extension
        schema_path = contracts_dir / f"{schema_name}.schema.json"
    
    if not schema_path.exists():
        return False, [f"Schema file not found: {schema_path}"]
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        return False, [f"Failed to load schema: {e}"]
    
    # Validate
    is_valid, errors = validate_json_against_schema(data, schema)
    
    if not is_valid:
        errors.insert(0, f"Validation failed for {output_path.name}:")
    
    return is_valid, errors


def run_validation(project_root: Path) -> Dict[str, Any]:
    """
    Run validation on all expected output files.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with validation results
    """
    contracts_dir = project_root / "contracts"
    processed_dir = project_root / "data" / "processed"
    
    # Define expected output files and their schemas
    validation_targets = [
        ("similarity_matrix.json", "similarity_report"),
        ("token_attribution_report.json", "token_attribution"),
        ("token_overlap.json", "token_attribution"),  # Uses same schema
        ("frequency_distributions_en.json", "frequency_distribution"),
        ("frequency_distributions_fr.json", "frequency_distribution"),
        ("frequency_distributions_zh.json", "frequency_distribution"),
        ("anisotropy_deviation.json", "anisotropy_report"),
        ("permutation_result.json", "permutation_result"),
        ("wals_validation.json", "wals_validation"),
    ]
    
    results = {
        "total": len(validation_targets),
        "passed": 0,
        "failed": 0,
        "missing": 0,
        "details": []
    }
    
    for filename, schema_name in validation_targets:
        output_path = processed_dir / filename
        schema_path = contracts_dir / f"{schema_name}.schema.yaml"
        
        # Check if schema exists
        if not schema_path.exists():
            schema_path = contracts_dir / f"{schema_name}.schema.json"
        
        schema_exists = schema_path.exists()
        
        detail = {
            "file": filename,
            "schema": schema_name,
            "schema_exists": schema_exists,
            "output_exists": output_path.exists(),
            "valid": False,
            "errors": []
        }
        
        if not schema_exists:
            detail["errors"].append(f"Schema file not found: {schema_path}")
            results["failed"] += 1
        elif not output_path.exists():
            detail["errors"].append(f"Output file not found: {output_path}")
            results["missing"] += 1
        else:
            is_valid, errors = validate_output_file(output_path, schema_name, contracts_dir)
            detail["valid"] = is_valid
            detail["errors"] = errors
            
            if is_valid:
                results["passed"] += 1
            else:
                results["failed"] += 1
        
        results["details"].append(detail)
    
    return results


def print_validation_results(results: Dict[str, Any]) -> None:
    """Print validation results in a human-readable format."""
    print("\n" + "=" * 60)
    print("SCHEMA VALIDATION RESULTS")
    print("=" * 60)
    print(f"Total files checked: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Missing: {results['missing']}")
    print("-" * 60)
    
    for detail in results["details"]:
        status = "✓ PASS" if detail["valid"] else "✗ FAIL"
        print(f"\n{status}: {detail['file']}")
        print(f"  Schema: {detail['schema']}")
        print(f"  Output exists: {detail['output_exists']}")
        print(f"  Schema exists: {detail['schema_exists']}")
        
        if detail["errors"]:
            print("  Errors:")
            for error in detail["errors"]:
                print(f"    - {error}")
    
    print("\n" + "=" * 60)
    
    if results["failed"] > 0 or results["missing"] > 0:
        print("VALIDATION FAILED")
        sys.exit(1)
    else:
        print("ALL VALIDATIONS PASSED")
        sys.exit(0)


def main():
    """Main entry point for the schema validator."""
    project_root = Path(__file__).parent.parent
    logger.info(f"Project root: {project_root}")
    
    results = run_validation(project_root)
    print_validation_results(results)


if __name__ == "__main__":
    main()
