"""
Schema validation utilities for the text-tone-emotional-support project.
Validates CSV and JSON data against YAML schemas defined in contracts/.
"""
import json
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml

from config import get_contracts_dir, get_raw_data_dir, get_processed_data_dir

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema file from the contracts directory."""
    contracts_dir = get_contracts_dir()
    schema_path = contracts_dir / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Basic JSON Schema validation (draft-07 compatible logic).
    Returns a list of error messages.
    Note: This is a lightweight implementation for critical fields.
    """
    errors = []
    
    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check properties types and constraints
    properties = schema.get('properties', {})
    for key, value in data.items():
        if key not in properties:
            if schema.get('additionalProperties') is False:
                errors.append(f"Unexpected property: {key}")
            continue
        
        prop_schema = properties[key]
        expected_type = prop_schema.get('type')
        
        # Type checking
        if expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Field '{key}' must be string, got {type(value).__name__}")
            if 'minLength' in prop_schema and len(value) < prop_schema['minLength']:
                errors.append(f"Field '{key}' too short")
            if 'pattern' in prop_schema:
                import re
                if not re.match(prop_schema['pattern'], value):
                    errors.append(f"Field '{key}' does not match pattern {prop_schema['pattern']}")
        elif expected_type == 'integer':
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(f"Field '{key}' must be integer, got {type(value).__name__}")
            if 'minimum' in prop_schema and value < prop_schema['minimum']:
                errors.append(f"Field '{key}' below minimum {prop_schema['minimum']}")
            if 'maximum' in prop_schema and value > prop_schema['maximum']:
                errors.append(f"Field '{key}' above maximum {prop_schema['maximum']}")
        elif expected_type == 'number':
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"Field '{key}' must be number, got {type(value).__name__}")
        elif expected_type == 'array':
            if not isinstance(value, list):
                errors.append(f"Field '{key}' must be array, got {type(value).__name__}")
        elif expected_type == 'object':
            if not isinstance(value, dict):
                errors.append(f"Field '{key}' must be object, got {type(value).__name__}")
        elif expected_type == 'boolean':
            if not isinstance(value, bool):
                errors.append(f"Field '{key}' must be boolean, got {type(value).__name__}")
        
        # Enum check
        if 'enum' in prop_schema:
            if value not in prop_schema['enum']:
                errors.append(f"Field '{key}' value '{value}' not in enum {prop_schema['enum']}")
    
    return errors

def validate_csv_against_schema(file_path: Path, schema_name: str) -> List[str]:
    """Validate a CSV file against a YAML schema."""
    schema = load_schema(schema_name)
    errors = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return errors

    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            # Check headers
            for field in required_fields:
                if field not in headers:
                    errors.append(f"CSV missing required column: {field}")
            
            for row_num, row in enumerate(reader, start=2):
                # Validate each row
                for field in required_fields:
                    value = row.get(field)
                    if value is None:
                        errors.append(f"Row {row_num}: Missing required field '{field}'")
                        continue
                    
                    if field in properties:
                        prop_schema = properties[field]
                        expected_type = prop_schema.get('type')
                        
                        # Type validation for CSV strings
                        if expected_type == 'integer':
                            try:
                                val = int(value)
                                if 'minimum' in prop_schema and val < prop_schema['minimum']:
                                    errors.append(f"Row {row_num}: {field} below min")
                                if 'maximum' in prop_schema and val > prop_schema['maximum']:
                                    errors.append(f"Row {row_num}: {field} above max")
                            except ValueError:
                                errors.append(f"Row {row_num}: {field} is not an integer")
                        elif expected_type == 'number':
                            try:
                                float(value)
                            except ValueError:
                                errors.append(f"Row {row_num}: {field} is not a number")
                        elif expected_type == 'string':
                            if 'minLength' in prop_schema and len(value) < prop_schema['minLength']:
                                errors.append(f"Row {row_num}: {field} too short")
                            if 'pattern' in prop_schema:
                                import re
                                if not re.match(prop_schema['pattern'], value):
                                    errors.append(f"Row {row_num}: {field} invalid format")
                        elif expected_type == 'enum':
                            if value not in prop_schema['enum']:
                                errors.append(f"Row {row_num}: {field} invalid enum value '{value}'")
    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")
    
    return errors

def main():
    """Run validation on all expected artifacts."""
    contracts_dir = get_contracts_dir()
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    
    all_errors = []
    
    # Validate Stimuli
    stimuli_file = raw_dir / "stimuli.csv"
    print(f"Validating {stimuli_file}...")
    errors = validate_csv_against_schema(stimuli_file, "stimulus.schema.yaml")
    if errors:
        all_errors.extend([f"Stimuli: {e}" for e in errors])
    else:
        print("  OK")
    
    # Validate Ratings
    ratings_file = raw_dir / "ratings.csv"
    print(f"Validating {ratings_file}...")
    errors = validate_csv_against_schema(ratings_file, "rating.schema.yaml")
    if errors:
        all_errors.extend([f"Ratings: {e}" for e in errors])
    else:
        print("  OK")
    
    # Validate Analysis Results
    analysis_file = processed_dir / "analysis_results.json"
    print(f"Validating {analysis_file}...")
    if analysis_file.exists():
        try:
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            errors = validate_json_against_schema(data, load_schema("analysis_result.schema.yaml"))
            if errors:
                all_errors.extend([f"Analysis: {e}" for e in errors])
            else:
                print("  OK")
        except json.JSONDecodeError:
            all_errors.append("Analysis: Invalid JSON")
    else:
        print("  Skipped (file not found)")
    
    if all_errors:
        print("\nValidation FAILED:")
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nValidation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
