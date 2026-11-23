"""
Schema Validator for BIDS events.tsv files.
Implements validation logic per T002d.
"""
import os
import sys
import json
import csv
import yaml
import hashlib
import logging
import jsonschema
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BEHAVIORAL_TASKS = {'Schandry', 'heartbeat'}
PHASE_TASKS = {'TSST', 'rest', 'baseline'}
ALL_VALID_TASKS = BEHAVIORAL_TASKS | PHASE_TASKS

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass

class FileLoadError(Exception):
    """Raised when a file cannot be loaded."""
    pass

class InvalidFormatError(Exception):
    """Raised when file format is invalid."""
    pass

def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
    """Load JSON/YAML schema from file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileLoadError(f"Schema file not found: {schema_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif path.suffix == '.json':
                return json.load(f)
            else:
                raise InvalidFormatError(f"Unsupported schema format: {path.suffix}")
    except Exception as e:
        raise FileLoadError(f"Failed to load schema: {e}")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise FileLoadError(f"Failed to calculate checksum: {e}")

def validate_data_against_schema(data: List[Dict], schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validate a list of row dictionaries against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required columns exist in at least one row (or header)
    # Since we are validating TSV content, we assume headers are present
    # and we check each row against the schema properties.
    
    # Schema validation using jsonschema
    # We validate each row as an object
    for i, row in enumerate(data):
        try:
            jsonschema.validate(instance=row, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Row {i}: {e.message} (path: {'/'.join(map(str, e.path))})")
        except Exception as e:
            errors.append(f"Row {i}: Unexpected validation error: {e}")
    
    return len(errors) == 0, errors

def validate_file_against_schema(
    file_path: str, 
    schema_path: str,
    log_checksum_to_state: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Validate a BIDS events.tsv file against the schema.
    
    Returns a structured object:
    {
        'valid': bool,
        'errors': list,
        'checksum': str,
        'behavioral_found': bool
    }
    
    Logic:
    - Exit code 0 if file exists and schema is valid (even if data content has errors)
    - Exit code 1 if file missing or schema validation fails (schema file missing)
    - behavioral_found: True if any row has task in BEHAVIORAL_TASKS
    """
    result = {
        'valid': False,
        'errors': [],
        'checksum': '',
        'behavioral_found': False
    }

    # 1. Check if file exists
    file_p = Path(file_path)
    if not file_p.exists():
        result['errors'].append(f"File not found: {file_path}")
        return result

    # 2. Load Schema
    try:
        schema = load_schema_from_file(schema_path)
    except FileLoadError as e:
        result['errors'].append(f"Schema error: {e}")
        return result
    except Exception as e:
        result['errors'].append(f"Unexpected schema error: {e}")
        return result

    # 3. Calculate Checksum
    try:
        checksum = calculate_sha256(file_path)
        result['checksum'] = checksum
        
        # Constitution Compliance: Log checksum to state if requested
        if log_checksum_to_state:
            logger.info(f"Checksum for {file_path}: {checksum}")
            # In a real implementation, this would update state/projects/...yaml
            # For now, we just log it as per requirement
    except FileLoadError as e:
        result['errors'].append(f"Checksum error: {e}")
        return result

    # 4. Load and Validate Data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
    except Exception as e:
        result['errors'].append(f"Failed to read TSV: {e}")
        return result

    if not rows:
        result['errors'].append("File is empty or has no data rows")
        return result

    # Validate against schema
    is_valid, validation_errors = validate_data_against_schema(rows, schema)
    result['valid'] = is_valid
    result['errors'].extend(validation_errors)

    # 5. Check for Behavioral Tasks
    behavioral_found = False
    for row in rows:
        task = row.get('task', '')
        if task in BEHAVIORAL_TASKS:
            behavioral_found = True
            break
        elif task not in ALL_VALID_TASKS:
            # If task is not in the enum, it's a validation error (already caught)
            # But we note if it's a known phase task
            pass

    result['behavioral_found'] = behavioral_found

    # Log specific phase vs behavioral findings
    if not behavioral_found:
        # Check if phase tasks exist
        phase_found = any(row.get('task') in PHASE_TASKS for row in rows)
        if phase_found:
            logger.info("Valid phase tasks (TSST/rest/baseline) found, but no behavioral tasks (Schandry/heartbeat).")
        else:
            logger.warning("No valid tasks found in events.tsv.")

    return result

def main():
    """
    CLI entry point for schema validator.
    Usage: python -m utils.schema_validator <events.tsv> <schema.yaml>
    Exit code 0: File exists, schema loaded, validation performed (regardless of data errors)
    Exit code 1: File missing, schema missing, or critical error
    """
    if len(sys.argv) < 3:
        print("Usage: python -m utils.schema_validator <events.tsv> <schema.yaml>")
        sys.exit(1)

    file_path = sys.argv[1]
    schema_path = sys.argv[2]

    try:
        result = validate_file_against_schema(file_path, schema_path, log_checksum_to_state=True)
        
        # Log results
        if result['valid']:
            logger.info(f"Validation PASSED for {file_path}")
        else:
            logger.warning(f"Validation FAILED for {file_path}: {result['errors']}")
        
        if result['behavioral_found']:
            logger.info("Behavioral task (Schandry/heartbeat) found.")
        else:
            logger.info("No behavioral task found (only phase tasks or none).")

        # Print JSON result for programmatic use
        print(json.dumps(result, indent=2))

        # Exit 0 if file existed and schema was valid (even if data had errors)
        # Exit 1 only if we couldn't even try to validate (missing file/schema)
        if result['errors'] and not result['checksum']:
            # Critical error (file missing, schema missing)
            sys.exit(1)
        
        sys.exit(0)

    except Exception as e:
        logger.error(f"Critical error during validation: {e}")
        print(json.dumps({'valid': False, 'errors': [str(e)], 'checksum': '', 'behavioral_found': False}))
        sys.exit(1)

if __name__ == "__main__":
    main()