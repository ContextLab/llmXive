"""
Schema validation for audit_report.json against contracts/audit_record.schema.yaml.
Implements FR-026: Add schema validation step after audit generation.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from code.src.contracts.validation import (
    SchemaValidator,
    get_audit_record_validator,
    get_default_logger,
)
from code.src.utils.logger import get_error_message, AuditLogger

# Error codes for schema validation failures
ERR_SCHEMA_MISSING = "ERR-200"
ERR_SCHEMA_INVALID = "ERR-201"
ERR_FILE_NOT_FOUND = "ERR-202"
ERR_FILE_READ = "ERR-203"

def load_audit_records_from_json(file_path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Load audit records from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing audit records.
        
    Returns:
        Tuple of (records_list, error_message).
        If successful, error_message is None.
    """
    logger = get_default_logger()
    
    if not file_path.exists():
        error_msg = get_error_message(ERR_FILE_NOT_FOUND)
        logger.error(f"{error_msg}: {file_path}")
        return [], error_msg
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both single record and list of records
        if isinstance(data, list):
            return data, None
        elif isinstance(data, dict):
            # If it's a single record wrapped in an object, extract the list
            if 'records' in data:
                return data['records'], None
            else:
                # Assume it's a single record
                return [data], None
        else:
            error_msg = get_error_message(ERR_SCHEMA_INVALID) + " Invalid JSON structure"
            logger.error(error_msg)
            return [], error_msg
            
    except json.JSONDecodeError as e:
        error_msg = get_error_message(ERR_FILE_READ) + f" JSON decode error: {str(e)}"
        logger.error(error_msg)
        return [], error_msg
    except Exception as e:
        error_msg = get_error_message(ERR_FILE_READ) + f" Unexpected error: {str(e)}"
        logger.error(error_msg)
        return [], error_msg

def validate_audit_report_schema(
    records: List[Dict[str, Any]], 
    schema_path: Optional[Path] = None
) -> Tuple[bool, List[str]]:
    """
    Validate audit records against the audit_record schema.
    
    Args:
        records: List of audit record dictionaries to validate.
        schema_path: Optional path to the schema file. If None, uses the default.
        
    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    logger = get_default_logger()
    errors = []
    
    if not records:
        logger.warning("No records to validate")
        return True, []
    
    # Get the validator for audit records
    validator, err = get_audit_record_validator(schema_path)
    if err:
        error_msg = get_error_message(ERR_SCHEMA_MISSING) + f" Schema validation setup failed: {err}"
        logger.error(error_msg)
        return False, [error_msg]
    
    # Validate each record
    for i, record in enumerate(records):
        is_valid, record_errors = validator.validate(record)
        if not is_valid:
            for error in record_errors:
                errors.append(f"Record {i}: {error}")
            logger.error(f"Validation failed for record {i}: {record_errors}")
    
    if errors:
        error_msg = get_error_message(ERR_SCHEMA_INVALID) + f" Found {len(errors)} validation errors"
        logger.error(error_msg)
        return False, errors
    
    logger.info(f"Successfully validated {len(records)} audit records")
    return True, []

def run_schema_validation(
    audit_report_path: Path,
    schema_path: Optional[Path] = None,
    strict_mode: bool = True
) -> Tuple[bool, str]:
    """
    Run schema validation on the audit report.
    
    Args:
        audit_report_path: Path to the audit_report.json file.
        schema_path: Optional path to the schema file. If None, uses the default.
        strict_mode: If True, fail on any validation error.
        
    Returns:
        Tuple of (success, message).
    """
    logger = get_default_logger()
    audit_logger = AuditLogger(logger)
    
    logger.info(f"Starting schema validation for {audit_report_path}")
    
    # Load the records
    records, load_error = load_audit_records_from_json(audit_report_path)
    if load_error:
        audit_logger.error(load_error)
        return False, load_error
    
    if not records:
        logger.warning("No records found in audit report")
        return True, "No records to validate"
    
    # Validate against schema
    is_valid, validation_errors = validate_audit_report_schema(records, schema_path)
    
    if not is_valid:
        error_details = "\n".join(validation_errors[:10])  # Show first 10 errors
        full_message = f"Schema validation failed with {len(validation_errors)} errors:\n{error_details}"
        audit_logger.error(get_error_message(ERR_SCHEMA_INVALID))
        return False, full_message
    
    logger.info("Schema validation passed")
    return True, "Schema validation successful"

def main() -> int:
    """
    Main entry point for schema validation.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate audit_report.json against the audit_record schema"
    )
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("output/audit_report.json"),
        help="Path to audit_report.json file"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("contracts/audit_record.schema.yaml"),
        help="Path to the schema file"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Fail on any validation error (default: True)"
    )
    
    args = parser.parse_args()
    
    success, message = run_schema_validation(
        args.input,
        args.schema,
        args.strict
    )
    
    if success:
        print(f"SUCCESS: {message}")
        return 0
    else:
        print(f"FAILED: {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
