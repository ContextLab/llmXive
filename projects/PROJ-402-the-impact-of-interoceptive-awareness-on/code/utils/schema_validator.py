"""
Schema Validator for BIDS events.tsv files.

This module validates BIDS events.tsv files against a JSON Schema definition.
It specifically distinguishes between valid behavioral tasks ('Schandry', 'heartbeat')
and valid phase tasks ('TSST', 'rest', 'baseline') as per project requirements.
"""
import os
import sys
import json
import csv
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for task classification
BEHAVIORAL_TASKS = {'schandry', 'heartbeat'}
PHASE_TASKS = {'tsst', 'rest', 'baseline'}
VALID_TASKS = BEHAVIORAL_TASKS.union(PHASE_TASKS)

class SchemaValidationError(Exception):
    """Raised when data does not conform to the schema."""
    pass

class FileLoadError(Exception):
    """Raised when a file cannot be loaded."""
    pass

class InvalidFormatError(Exception):
    """Raised when a file format is invalid."""
    pass

def load_schema_from_file(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        The loaded schema as a dictionary.
        
    Raises:
        FileLoadError: If the file cannot be read or parsed.
    """
    if not schema_path.exists():
        raise FileLoadError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            if schema_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except yaml.YAMLError as e:
        raise FileLoadError(f"Failed to parse YAML schema: {e}")
    except json.JSONDecodeError as e:
        raise FileLoadError(f"Failed to parse JSON schema: {e}")
    except Exception as e:
        raise FileLoadError(f"Unexpected error loading schema: {e}")

def validate_contract_input(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate input data against the schema without external dependencies.
    This is a simplified validator that checks required fields and types.
    
    Args:
        data: List of row dictionaries.
        schema: The JSON Schema dictionary.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    if not schema or 'properties' not in schema:
        errors.append("Schema is missing 'properties' definition")
        return False, errors
    
    properties = schema['properties']
    required_fields = schema.get('required', [])
    
    # Check required fields presence
    for field in required_fields:
        if field not in properties:
            errors.append(f"Required field '{field}' not found in schema properties")
    
    # Validate each row
    for i, row in enumerate(data):
        # Check required fields in data
        for field in required_fields:
            if field not in row:
                errors.append(f"Row {i}: Missing required field '{field}'")
        
        # Validate 'task' field specifically
        if 'task' in row:
            task_value = row['task'].lower() if isinstance(row['task'], str) else str(row['task']).lower()
            
            # Check if task is in valid set
            if task_value not in VALID_TASKS:
                errors.append(f"Row {i}: Invalid task value '{row['task']}'. "
                            f"Must be one of: {sorted(VALID_TASKS)}")
            
            # Specific logic for behavioral vs phase tasks
            if task_value in PHASE_TASKS:
                # Log that this is a phase task, not behavioral
                logger.debug(f"Row {i}: Task '{row['task']}' identified as a phase task, not a behavioral task.")
            elif task_value in BEHAVIORAL_TASKS:
                logger.debug(f"Row {i}: Task '{row['task']}' identified as a behavioral task.")
        
        # Validate numeric fields if present
        for field in ['onset', 'duration', 'value']:
            if field in row:
                try:
                    val = float(row[field])
                    # Check schema constraints if defined
                    field_schema = properties.get(field, {})
                    if 'minimum' in field_schema and val < field_schema['minimum']:
                        errors.append(f"Row {i}: Field '{field}' value {val} is below minimum {field_schema['minimum']}")
                except (ValueError, TypeError):
                    errors.append(f"Row {i}: Field '{field}' must be numeric, got '{row[field]}'")
        
        # Validate string fields if present
        for field in ['trial_type']:
            if field in row:
                if not isinstance(row[field], str):
                    errors.append(f"Row {i}: Field '{field}' must be a string")
    
    return len(errors) == 0, errors

def validate_data_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Wrapper for validate_contract_input to maintain API compatibility.
    """
    return validate_contract_input(data, schema)

def validate_file_against_schema(file_path: Path, schema_path: Path) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate a BIDS events.tsv file against a schema.
    
    Args:
        file_path: Path to the events.tsv file.
        schema_path: Path to the schema file.
        
    Returns:
        Tuple of (is_valid, list_of_errors, summary_stats).
        
    Raises:
        FileLoadError: If files cannot be read.
        InvalidFormatError: If the TSV format is invalid.
    """
    # Load schema
    try:
        schema = load_schema_from_file(schema_path)
    except FileLoadError as e:
        logger.error(f"Schema loading failed: {e}")
        raise
    
    # Load TSV file
    if not file_path.exists():
        raise FileLoadError(f"Events file not found: {file_path}")
    
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                # Convert numeric strings to float where appropriate
                cleaned_row = {}
                for key, value in row.items():
                    if key in ['onset', 'duration', 'value'] and value:
                        try:
                            cleaned_row[key] = float(value)
                        except ValueError:
                            cleaned_row[key] = value
                    else:
                        cleaned_row[key] = value
                data.append(cleaned_row)
    except Exception as e:
        raise InvalidFormatError(f"Failed to parse TSV file: {e}")
    
    if not data:
        logger.warning(f"File {file_path} is empty or has no data rows")
        # Still validate structure if schema requires specific columns
        # For now, treat empty file as valid but warn
    
    # Validate data
    is_valid, errors = validate_data_against_schema(data, schema)
    
    # Generate summary stats
    summary_stats = {
        'file': str(file_path),
        'total_rows': len(data),
        'behavioral_tasks_found': [],
        'phase_tasks_found': [],
        'invalid_tasks_found': []
    }
    
    for row in data:
        if 'task' in row:
            task_val = row['task'].lower() if isinstance(row['task'], str) else str(row['task']).lower()
            if task_val in BEHAVIORAL_TASKS:
                if task_val not in summary_stats['behavioral_tasks_found']:
                    summary_stats['behavioral_tasks_found'].append(task_val)
            elif task_val in PHASE_TASKS:
                if task_val not in summary_stats['phase_tasks_found']:
                    summary_stats['phase_tasks_found'].append(task_val)
            else:
                if task_val not in summary_stats['invalid_tasks_found']:
                    summary_stats['invalid_tasks_found'].append(task_val)
    
    return is_valid, errors, summary_stats

def main():
    """
    Main entry point for command-line usage.
    Validates a single events.tsv file against the schema.
    
    Usage:
        python -m utils.schema_validator <path_to_events.tsv> [path_to_schema.yaml]
    
    Exit codes:
        0: Validation successful
        1: Validation failed
        2: File not found
        3: Schema not found
    """
    if len(sys.argv) < 2:
        print("Usage: python -m utils.schema_validator <events.tsv> [schema.yaml]")
        print("  If schema.yaml is omitted, defaults to contracts/dataset.schema.yaml")
        sys.exit(2)
    
    events_file = Path(sys.argv[1])
    schema_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("contracts/dataset.schema.yaml")
    
    # Resolve paths relative to project root if needed
    if not events_file.is_absolute():
        events_file = Path.cwd() / events_file
    if not schema_file.is_absolute():
        schema_file = Path.cwd() / schema_file
    
    try:
        is_valid, errors, stats = validate_file_against_schema(events_file, schema_file)
        
        print(f"\nValidation Results for: {events_file}")
        print(f"Schema: {schema_file}")
        print("-" * 50)
        
        if stats['total_rows'] > 0:
            print(f"Total Rows: {stats['total_rows']}")
            if stats['behavioral_tasks_found']:
                print(f"Behavioral Tasks Found: {', '.join(stats['behavioral_tasks_found'])}")
            if stats['phase_tasks_found']:
                print(f"Phase Tasks Found: {', '.join(stats['phase_tasks_found'])}")
            if stats['invalid_tasks_found']:
                print(f"Invalid Tasks Found: {', '.join(stats['invalid_tasks_found'])}")
        
        if is_valid:
            print("\n✓ Validation PASSED")
            sys.exit(0)
        else:
            print("\n✗ Validation FAILED")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
            
    except FileLoadError as e:
        print(f"\n✗ File Load Error: {e}")
        sys.exit(3 if "schema" in str(e).lower() else 2)
    except InvalidFormatError as e:
        print(f"\n✗ Invalid Format Error: {e}")
        sys.exit(4)
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        sys.exit(5)

if __name__ == "__main__":
    main()
