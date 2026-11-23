"""
Validation module for checking data against JSON schemas.
Implements T017 and T017b validation gates.
"""
import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add code directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: jsonschema module not found. Please install it via 'pip install jsonschema'.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in schema file {schema_path}: {e}")
        raise

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a single record against a schema.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate(instance=record, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e.message)

def validate_aligned_events(csv_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """Validate all records in a CSV file against a schema.
    
    Args:
        csv_path: Path to the CSV file to validate
        schema_path: Path to the JSON schema file
        
    Returns:
        Tuple of (all_valid, list_of_errors)
    """
    import csv
    
    schema = load_schema(schema_path)
    errors = []
    total_records = 0
    valid_records = 0
    
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False, [f"File not found: {csv_path}"]
    
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate header against schema required fields if applicable
            if 'required' in schema.get('properties', {}):
                required_fields = schema['properties']['required']
                header_fields = set(reader.fieldnames or [])
                # Note: Schema validation for CSV headers is complex; we'll validate records primarily
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                total_records += 1
                is_valid, error_msg = validate_record(row, schema)
                
                if is_valid:
                    valid_records += 1
                else:
                    errors.append(f"Row {row_num}: {error_msg}")
                    # Limit error reporting to first 10 errors to avoid log flooding
                    if len(errors) >= 10:
                        errors.append("... (additional errors truncated)")
                        break
    
    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}")
        return False, [f"Error reading file: {str(e)}"]
    
    logger.info(f"Validation complete: {valid_records}/{total_records} records valid")
    
    if errors:
        logger.error(f"Validation failed with {len(errors)} errors")
        return False, errors
    
    return True, []

def block_write_if_invalid(csv_path: str, schema_path: str) -> bool:
    """Validate a file and block if invalid.
    
    Args:
        csv_path: Path to the CSV file to validate
        schema_path: Path to the JSON schema file
        
    Returns:
        True if valid, False if invalid
    """
    is_valid, errors = validate_aligned_events(csv_path, schema_path)
    
    if not is_valid:
        logger.error("Validation failed. Blocking write operation.")
        for err in errors[:5]:  # Log first 5 errors
            logger.error(f"  - {err}")
        return False
    
    logger.info("Validation passed. Proceeding with write operation.")
    return True

def main():
    """Main entry point for validation script.
    
    Usage:
        python validate.py <csv_path> <schema_path>
        
    Returns:
        0 if validation passes, 1 if it fails
    """
    if len(sys.argv) != 3:
        print("Usage: python validate.py <csv_path> <schema_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    schema_path = sys.argv[2]
    
    logger.info(f"Validating {csv_path} against {schema_path}")
    
    is_valid, errors = validate_aligned_events(csv_path, schema_path)
    
    if not is_valid:
        logger.error("Validation FAILED")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)
    
    logger.info("Validation PASSED")
    sys.exit(0)

if __name__ == "__main__":
    main()