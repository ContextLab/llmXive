"""
Export Schema Validator Module (T057)

Validates the generated audit_report.json against the contracts/audit_record.schema.yaml
schema as required by FR-026.
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
from code.src.utils.logger import AuditLogger, get_error_message

def load_audit_records_from_json(
    file_path: Path, logger: Optional[AuditLogger] = None
) -> List[Dict[str, Any]]:
    """
    Load audit records from a JSON file.

    Args:
        file_path: Path to the audit_report.json file.
        logger: Optional logger instance.

    Returns:
        List of audit record dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if logger is None:
        logger = get_default_logger()

    if not file_path.exists():
        logger.error("ERR-202", f"Audit report file not found: {file_path}")
        raise FileNotFoundError(f"Audit report file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "records" in data:
        return data["records"]
    else:
        logger.error("ERR-203", "Invalid audit report structure: expected list or dict with 'records' key")
        raise ValueError("Invalid audit report structure")

def validate_audit_report_schema(
    audit_records: List[Dict[str, Any]],
    schema_path: Optional[Path] = None,
    logger: Optional[AuditLogger] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate audit records against the audit_record schema.

    Args:
        audit_records: List of audit record dictionaries to validate.
        schema_path: Optional path to the schema file. If None, uses default.
        logger: Optional logger instance.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    if logger is None:
        logger = get_default_logger()

    if schema_path is None:
        schema_path = Path("code/contracts/audit_record.schema.yaml")

    if not schema_path.exists():
        error_msg = f"Schema file not found: {schema_path}"
        logger.error("ERR-204", error_msg)
        return False, [error_msg]

    try:
        validator = get_audit_record_validator(schema_path)
    except Exception as e:
        error_msg = f"Failed to load schema validator: {str(e)}"
        logger.error("ERR-205", error_msg)
        return False, [error_msg]

    errors = []
    for i, record in enumerate(audit_records):
        is_valid, validation_errors = validator.validate(record)
        if not is_valid:
            for err in validation_errors:
                errors.append(f"Record {i}: {err}")

    if errors:
        logger.error("ERR-206", f"Schema validation failed with {len(errors)} errors")
        return False, errors

    logger.info("Schema validation passed successfully")
    return True, []

def run_schema_validation(
    audit_report_path: Path,
    schema_path: Optional[Path] = None,
    exit_on_failure: bool = True,
) -> int:
    """
    Run schema validation on the audit report.

    Args:
        audit_report_path: Path to the audit_report.json file.
        schema_path: Optional path to the schema file.
        exit_on_failure: If True, exit with code 1 on validation failure.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger = get_default_logger()
    logger.info(f"Starting schema validation for {audit_report_path}")

    try:
        records = load_audit_records_from_json(audit_report_path, logger)
        logger.info(f"Loaded {len(records)} audit records")
    except Exception as e:
        logger.error("ERR-207", f"Failed to load audit report: {str(e)}")
        if exit_on_failure:
            sys.exit(1)
        return 1

    is_valid, errors = validate_audit_report_schema(records, schema_path, logger)

    if not is_valid:
        logger.error("ERR-208", "Schema validation failed")
        for error in errors:
            logger.error("ERR-208", error)
        if exit_on_failure:
            sys.exit(1)
        return 1

    logger.info("Schema validation completed successfully")
    return 0

def main() -> int:
    """Main entry point for schema validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate audit_report.json against the audit_record schema"
    )
    parser.add_argument(
        "--audit-report",
        type=Path,
        default=Path("code/output/audit_report.json"),
        help="Path to the audit report JSON file",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to the schema file (default: contracts/audit_record.schema.yaml)",
    )
    parser.add_argument(
        "--no-exit",
        action="store_true",
        help="Do not exit with code 1 on validation failure",
    )

    args = parser.parse_args()

    return run_schema_validation(
        args.audit_report,
        args.schema,
        exit_on_failure=not args.no_exit,
    )

if __name__ == "__main__":
    sys.exit(main())
