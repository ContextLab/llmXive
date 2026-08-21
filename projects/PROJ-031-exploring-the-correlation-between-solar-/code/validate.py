import os
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validate.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str = "contracts/aligned_event.schema.yaml") -> Dict[str, Any]:
    """Load validation schema from YAML file."""
    import yaml
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single record against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_fields = schema.get("required", [])
    field_types = schema.get("properties", {})
    
    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Check field types (simplified validation)
    for field, value in record.items():
        if field in field_types:
            expected_type = field_types[field].get("type")
            if expected_type == "string":
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
            elif expected_type == "number":
                # Allow int or float for numbers
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
            elif expected_type == "integer":
                if not isinstance(value, int):
                    errors.append(f"Field '{field}' should be integer, got {type(value).__name__}")
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' should be boolean, got {type(value).__name__}")
    
    return len(errors) == 0, errors

def validate_aligned_events(
    csv_path: str = "data/processed/aligned_events.csv",
    schema_path: str = "contracts/aligned_event.schema.yaml"
) -> Tuple[bool, int, int, List[Dict[str, Any]]]:
    """
    Validate all records in aligned_events.csv against the schema.
    Returns (is_valid, total_records, valid_records, error_details).
    """
    import yaml
    import csv
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    schema = load_schema(schema_path)
    
    total_records = 0
    valid_records = 0
    error_details = []
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            total_records += 1
            is_valid, errors = validate_record(row, schema)
            if is_valid:
                valid_records += 1
            else:
                error_details.append({
                    "row": i + 1,
                    "errors": errors
                })
    
    is_valid = (total_records > 0 and valid_records == total_records)
    return is_valid, total_records, valid_records, error_details

def block_write_if_invalid(
    csv_path: str = "data/processed/aligned_events.csv",
    schema_path: str = "contracts/aligned_event.schema.yaml"
) -> bool:
    """
    Validate the CSV file and block further processing if invalid.
    Returns True if valid (processing can continue), False if invalid.
    
    This function is designed to be called BEFORE writing the final CSV
    or updating the manifest. If it returns False, the caller MUST abort
    the write operation.
    """
    try:
        is_valid, total, valid, errors = validate_aligned_events(csv_path, schema_path)
        
        if not is_valid:
            logger.error(f"Validation FAILED: {valid}/{total} records valid")
            logger.error(f"First 5 errors: {errors[:5]}")
            
            # Log detailed errors
            for err in errors[:10]:
                logger.error(f"Row {err['row']}: {err['errors']}")
            
            if len(errors) > 10:
                logger.error(f"... and {len(errors) - 10} more errors")
            
            return False
        
        logger.info(f"Validation PASSED: {valid}/{total} records valid")
        return True
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        # If schema loading fails or file missing, we must block
        return False

def main():
    """Main entry point for validation."""
    csv_path = "data/processed/aligned_events.csv"
    schema_path = "contracts/aligned_event.schema.yaml"
    
    logger.info(f"Validating {csv_path} against {schema_path}")
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        print(f"Error: {csv_path} not found. Run align.py first.")
        sys.exit(1)
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        print(f"Error: {schema_path} not found. Create schema first.")
        sys.exit(1)
    
    is_valid, total, valid, errors = validate_aligned_events(csv_path, schema_path)
    
    if is_valid:
        print(f"✓ Validation PASSED: {valid}/{total} records valid")
        sys.exit(0)
    else:
        print(f"✗ Validation FAILED: {valid}/{total} records valid")
        print(f"First 5 errors:")
        for err in errors[:5]:
            print(f"  Row {err['row']}: {err['errors']}")
        sys.exit(1)

if __name__ == "__main__":
    main()