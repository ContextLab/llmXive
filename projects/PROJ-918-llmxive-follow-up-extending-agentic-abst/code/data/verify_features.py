import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Set

import pyarrow.parquet as pq
import yaml

logger = logging.getLogger(__name__)

# Configuration constants
MAX_STRING_LENGTH = 500  # Threshold to flag potential full context strings
CRITICAL_COLUMNS = {"search_count", "error_frequency", "token_usage", "turn_number", "abstention_label"}


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the dataset schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    return schema


def validate_schema_compliance(
    table: pq.Table, 
    schema: Dict[str, Any]
) -> List[str]:
    """
    Validate that the Parquet table matches the schema definition.
    Returns a list of errors (empty if valid).
    """
    errors = []
    schema_fields = schema.get("fields", {})
    table_schema = table.schema
    table_columns = set(table.column_names)
    schema_columns = set(schema_fields.keys())

    # Check for missing columns
    missing_cols = schema_columns - table_columns
    if missing_cols:
        errors.append(f"Missing columns required by schema: {missing_cols}")

    # Check for extra columns not in schema (optional strictness)
    extra_cols = table_columns - schema_columns
    if extra_cols:
        logger.warning(f"Extra columns found in data not in schema: {extra_cols}")

    # Check data types for critical columns
    for col_name, col_type in schema_fields.items():
        if col_name in table_columns:
            idx = table.column_names.index(col_name)
            actual_type = table_schema.field(idx).type
            # Simple type mapping check (pyarrow types vs schema string types)
            # This is a simplified check; a robust one would map pyarrow types to schema types
            expected_type_str = col_type.get("type", "")
            
            # Basic mapping for common types
            type_map = {
                "int64": ["int64"],
                "float64": ["double", "float"],
                "string": ["string"],
                "bool": ["bool"]
            }
            
            if expected_type_str in type_map:
                if actual_type not in type_map[expected_type_str]:
                    errors.append(
                        f"Column '{col_name}' has type {actual_type}, expected {expected_type_str}"
                    )
            else:
                logger.warning(f"Unknown expected type '{expected_type_str}' for '{col_name}'")

    return errors


def detect_full_context_strings(
    table: pq.Table, 
    threshold: int = MAX_STRING_LENGTH
) -> Dict[str, List[Any]]:
    """
    Scan string columns for values exceeding a length threshold,
    which likely indicates full semantic context leakage.
    Returns a dict of column_name -> list of offending values (truncated).
    """
    violations = {}
    
    for col_name in table.column_names:
        col = table.column(col_name)
        if col.type == "string":
            offending_values = []
            for i, val in enumerate(col):
                if val is not None and len(val) > threshold:
                    # Store a truncated version for the report to avoid huge logs
                    offending_values.append(f"[{len(val)} chars] {val[:100]}...")
            
            if offending_values:
                violations[col_name] = offending_values[:10]  # Limit report size
    
    return violations


def generate_report(
    schema_path: Path,
    data_path: Path,
    output_path: Path
) -> bool:
    """
    Main verification routine.
    Returns True if verification passes, False otherwise.
    Writes a JSON report to output_path.
    """
    report = {
        "schema_path": str(schema_path),
        "data_path": str(data_path),
        "passed": False,
        "errors": [],
        "warnings": [],
        "full_context_violations": {}
    }

    try:
        # 1. Load Schema
        logger.info(f"Loading schema from {schema_path}")
        schema = load_schema(schema_path)

        # 2. Load Data
        logger.info(f"Loading data from {data_path}")
        table = pq.read_table(data_path)
        logger.info(f"Loaded {table.num_rows} rows, columns: {table.column_names}")

        # 3. Validate Schema Compliance
        schema_errors = validate_schema_compliance(table, schema)
        if schema_errors:
            report["errors"].extend(schema_errors)
            logger.error(f"Schema validation failed: {schema_errors}")
        else:
            logger.info("Schema validation passed.")

        # 4. Detect Full Context Strings
        violations = detect_full_context_strings(table)
        if violations:
            report["full_context_violations"] = violations
            report["errors"].append(
                f"Detected full semantic context strings in columns: {list(violations.keys())}"
            )
            logger.error(f"Full context strings detected: {list(violations.keys())}")
        else:
            logger.info("No full semantic context strings detected.")

        # 5. Check Critical Columns Presence (Specific to task T017/FR-001)
        missing_critical = CRITICAL_COLUMNS - set(table.column_names)
        if missing_critical:
            report["errors"].append(
                f"Critical columns missing: {missing_critical}"
            )
            logger.error(f"Missing critical columns: {missing_critical}")

        # Determine Pass/Fail
        if not report["errors"]:
            report["passed"] = True
            logger.info("Verification PASSED: No schema violations or full context strings.")
        else:
            report["passed"] = False
            logger.error("Verification FAILED.")

    except Exception as e:
        logger.exception(f"Verification process failed with exception: {e}")
        report["errors"].append(f"Critical error during verification: {str(e)}")

    # Write Report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report written to {output_path}")
    return report["passed"]


def main():
    """Entry point for CLI execution."""
    logging.basicConfig(level=logging.INFO)
    
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    data_path = project_root / "data" / "processed" / "features.parquet"
    output_path = project_root / "data" / "processed" / "verification_report.json"

    # Allow override via CLI args
    if len(sys.argv) >= 3:
        schema_path = Path(sys.argv[1])
        data_path = Path(sys.argv[2])
    if len(sys.argv) >= 4:
        output_path = Path(sys.argv[3])

    success = generate_report(schema_path, data_path, output_path)
    
    # Exit with error code if verification failed
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
