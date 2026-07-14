import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

from utils.schemas import get_schema_path, load_schema
from config import get_config_summary


def validate_field_type(value: Any, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value matches the expected JSON Schema type.

    Args:
        value: The value to validate.
        expected_type: The expected type string (e.g., 'string', 'integer', 'boolean', 'array', 'object', 'null').

    Returns:
        Tuple of (is_valid, error_message).
    """
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }

    if expected_type not in type_map:
        return False, f"Unknown type: {expected_type}"

    expected_python_type = type_map[expected_type]

    # Special handling for integer vs number (Python bool is subclass of int)
    if expected_type == "integer" and isinstance(value, bool):
        return False, f"Expected integer, got boolean"

    if not isinstance(value, expected_python_type):
        return False, f"Expected {expected_type}, got {type(value).__name__}"

    return True, None


def validate_record_against_schema(
    record: Dict[str, Any],
    schema: Dict[str, Any],
    record_id: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate a single record against a JSON Schema.

    Args:
        record: The record to validate.
        schema: The JSON Schema definition.
        record_id: Optional identifier for the record (e.g., line number or issue_id).

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    prefix = f"Record {record_id}: " if record_id else ""

    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in record:
            errors.append(f"{prefix}Missing required field: {field}")

    # Validate each field
    properties = schema.get("properties", {})
    for field_name, value in record.items():
        if field_name not in properties:
            # Extra field - could be an error or warning depending on strictness
            # For now, we'll just warn but not fail
            continue

        field_schema = properties[field_name]
        field_type = field_schema.get("type")

        if field_type:
            is_valid, error_msg = validate_field_type(value, field_type)
            if not is_valid:
                errors.append(f"{prefix}Field '{field_name}': {error_msg}")

        # Validate array items if applicable
        if field_type == "array" and "items" in field_schema:
            if isinstance(value, list):
                items_schema = field_schema["items"]
                items_type = items_schema.get("type")
                for idx, item in enumerate(value):
                    is_valid, error_msg = validate_field_type(item, items_type)
                    if not is_valid:
                        errors.append(f"{prefix}Field '{field_name}'[{idx}]: {error_msg}")

    return len(errors) == 0, errors


def validate_jsonl_against_schema(
    file_path: Path,
    schema_name: str,
    max_errors: int = 10
) -> Tuple[bool, List[str], int]:
    """
    Validate a JSONL file against a schema.

    Args:
        file_path: Path to the JSONL file.
        schema_name: Name of the schema (e.g., 'dataset_schema', 'agent_log_schema').
        max_errors: Maximum number of errors to report before stopping.

    Returns:
        Tuple of (is_valid, list_of_error_messages, total_records_checked).
    """
    schema = load_schema(schema_name)
    errors = []
    total_records = 0

    if not file_path.exists():
        return False, [f"File not found: {file_path}"], 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            total_records += 1

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                if len(errors) >= max_errors:
                    break
                continue

            is_valid, record_errors = validate_record_against_schema(
                record, schema, record_id=f"line {line_num}"
            )

            if not is_valid:
                errors.extend(record_errors)
                if len(errors) >= max_errors:
                    break

    return len(errors) == 0, errors, total_records


def validate_parquet_against_schema(
    file_path: Path,
    schema_name: str,
    max_errors: int = 10
) -> Tuple[bool, List[str], int]:
    """
    Validate a Parquet file against a schema.

    Args:
        file_path: Path to the Parquet file.
        schema_name: Name of the schema (e.g., 'dataset_schema', 'result_schema').
        max_errors: Maximum number of errors to report before stopping.

    Returns:
        Tuple of (is_valid, list_of_error_messages, total_records_checked).
    """
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        return False, ["PyArrow or Pandas not installed. Install with: pip install pandas pyarrow"], 0

    schema = load_schema(schema_name)
    errors = []
    total_records = 0

    if not file_path.exists():
        return False, [f"File not found: {file_path}"], 0

    try:
        table = pq.read_table(file_path)
        df = table.to_pandas()
    except Exception as e:
        return False, [f"Failed to read Parquet file: {e}"], 0

    total_records = len(df)

    # Validate column types
    properties = schema.get("properties", {})
    for col_name in df.columns:
        if col_name not in properties:
            # Extra column - warning
            continue

        field_schema = properties[col_name]
        expected_type = field_schema.get("type")

        if expected_type:
            actual_type = str(df[col_name].dtype)

            # Map schema types to pandas dtypes
            type_map = {
                "string": ["object", "string"],
                "integer": ["int64", "int32", "int16", "int8"],
                "number": ["float64", "float32"],
                "boolean": ["bool"],
                "array": ["object"],  # Arrays are often stored as lists in object dtype
                "object": ["object"]
            }

            expected_dtypes = type_map.get(expected_type, [])
            if expected_dtypes and actual_type not in expected_dtypes:
                errors.append(f"Column '{col_name}': Expected {expected_type}, got {actual_type}")
                if len(errors) >= max_errors:
                    break

    # Validate individual records (sample-based for large files)
    sample_size = min(100, total_records)
    if sample_size > 0:
        sample_df = df.head(sample_size)
        for idx, row in sample_df.iterrows():
            record = row.to_dict()
            is_valid, record_errors = validate_record_against_schema(
                record, schema, record_id=f"row {idx}"
            )
            if not is_valid:
                errors.extend(record_errors)
                if len(errors) >= max_errors:
                    break

    return len(errors) == 0, errors, total_records


def validate_dataset_artifact(
    file_path: Path,
    schema_name: str
) -> Dict[str, Any]:
    """
    Validate a dataset artifact (JSONL or Parquet) against its schema.

    Args:
        file_path: Path to the artifact file.
        schema_name: Name of the schema to validate against.

    Returns:
        Dictionary with validation results.
    """
    result = {
        "file": str(file_path),
        "schema": schema_name,
        "valid": False,
        "errors": [],
        "record_count": 0,
        "file_type": None
    }

    suffix = file_path.suffix.lower()

    if suffix == ".jsonl":
        is_valid, errors, count = validate_jsonl_against_schema(file_path, schema_name)
        result["file_type"] = "jsonl"
        result["record_count"] = count
        result["errors"] = errors
        result["valid"] = is_valid

    elif suffix == ".parquet":
        is_valid, errors, count = validate_parquet_against_schema(file_path, schema_name)
        result["file_type"] = "parquet"
        result["record_count"] = count
        result["errors"] = errors
        result["valid"] = is_valid

    else:
        result["errors"] = [f"Unsupported file type: {suffix}"]

    return result


def validate_all_curated_artifacts(
    curated_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Validate all curated artifacts in the data/curated directory.

    Args:
        curated_dir: Path to the curated directory (defaults to data/curated).

    Returns:
        Dictionary with validation results for all artifacts.
    """
    if curated_dir is None:
        curated_dir = Path("data/curated")

    if not curated_dir.exists():
        return {
            "directory": str(curated_dir),
            "valid": False,
            "error": f"Directory not found: {curated_dir}",
            "artifacts": []
        }

    # Define artifact-to-schema mappings
    artifact_mappings = {
        "hard_subset.jsonl": "dataset_schema",
        "synthetic_issues.jsonl": "dataset_schema",
        "ground_truth.jsonl": "dataset_schema",
        "agent_logs.jsonl": "agent_log_schema",
        "results.jsonl": "result_schema"
    }

    results = {
        "directory": str(curated_dir),
        "artifacts": [],
        "all_valid": True
    }

    for filename, schema_name in artifact_mappings.items():
        file_path = curated_dir / filename
        if file_path.exists():
            artifact_result = validate_dataset_artifact(file_path, schema_name)
            results["artifacts"].append(artifact_result)
            if not artifact_result["valid"]:
                results["all_valid"] = False
        else:
            results["artifacts"].append({
                "file": filename,
                "schema": schema_name,
                "valid": False,
                "errors": [f"File not found: {file_path}"],
                "record_count": 0
            })
            results["all_valid"] = False

    return results


def generate_validation_report(
    validation_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate a Markdown validation report.

    Args:
        validation_results: Results from validate_all_curated_artifacts.
        output_path: Path to write the report.
    """
    report_lines = [
        "# Data Validation Report",
        "",
        f"**Generated:** {get_config_summary().get('timestamp', 'N/A')}",
        f"**Directory:** {validation_results.get('directory', 'N/A')}",
        "",
        f"**Overall Status:** {'✅ PASSED' if validation_results.get('all_valid', False) else '❌ FAILED'}",
        "",
        "## Artifact Details",
        ""
    ]

    for artifact in validation_results.get("artifacts", []):
        status = "✅" if artifact.get("valid", False) else "❌"
        report_lines.append(f"### {status} {artifact.get('file', 'Unknown')}")
        report_lines.append(f"- **Schema:** {artifact.get('schema', 'N/A')}")
        report_lines.append(f"- **Type:** {artifact.get('file_type', 'N/A')}")
        report_lines.append(f"- **Records:** {artifact.get('record_count', 0)}")

        errors = artifact.get("errors", [])
        if errors:
            report_lines.append("")
            report_lines.append("**Errors:**")
            for error in errors[:10]:  # Limit errors
                report_lines.append(f"- {error}")
            if len(errors) > 10:
                report_lines.append(f"- ... and {len(errors) - 10} more")
        else:
            report_lines.append("- No errors found.")

        report_lines.append("")

    # Write report
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))


def main():
    """
    CLI entry point for validation module.
    Usage: python -m code.utils.validation [options]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate data artifacts against schemas")
    parser.add_argument(
        "--curated-dir",
        type=Path,
        default=Path("data/curated"),
        help="Path to curated data directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/curated/validation_report.md"),
        help="Path to output validation report"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of Markdown"
    )

    args = parser.parse_args()

    print(f"Validating artifacts in: {args.curated_dir}")
    results = validate_all_curated_artifacts(args.curated_dir)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        generate_validation_report(results, args.output)
        print(f"Validation report saved to: {args.output}")

    sys.exit(0 if results.get("all_valid", False) else 1)


if __name__ == "__main__":
    main()