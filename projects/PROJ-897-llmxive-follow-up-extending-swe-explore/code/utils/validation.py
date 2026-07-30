"""
Validation utilities for JSONL/Parquet schema validation against contracts.
Implements strict schema enforcement for data artifacts.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

from config import get_path, get_config_summary, DATA_CURATED, DATA_RAW, DATA_RESULTS
from utils.schemas import get_schema_path, load_schema


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON schema type.

    Args:
        value: The value to validate.
        expected_type: The expected type (string, integer, number, boolean, array, object, null).

    Returns:
        True if the type matches, False otherwise.
    """
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    if expected_type not in type_map:
        return False

    expected_python_type = type_map[expected_type]
    return isinstance(value, expected_python_type)


def validate_record_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a JSON schema definition.

    Args:
        record: The record to validate.
        schema: The JSON schema definition.

    Returns:
        A list of validation error messages. Empty if valid.
    """
    errors = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check field types and constraints
    for field, value in record.items():
        if field not in properties:
            # Optional: warn about extra fields or skip
            continue

        field_schema = properties[field]
        expected_type = field_schema.get("type")

        if expected_type:
            if not validate_field_type(value, expected_type):
                errors.append(
                    f"Field '{field}' has type {type(value).__name__}, expected {expected_type}"
                )

        # Check for string constraints
        if expected_type == "string" and isinstance(value, str):
            if "minLength" in field_schema and len(value) < field_schema["minLength"]:
                errors.append(
                    f"Field '{field}' length {len(value)} is less than minLength {field_schema['minLength']}"
                )
            if "maxLength" in field_schema and len(value) > field_schema["maxLength"]:
                errors.append(
                    f"Field '{field}' length {len(value)} exceeds maxLength {field_schema['maxLength']}"
                )

        # Check for numeric constraints
        if expected_type in ("integer", "number") and isinstance(value, (int, float)):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                errors.append(
                    f"Field '{field}' value {value} is less than minimum {field_schema['minimum']}"
                )
            if "maximum" in field_schema and value > field_schema["maximum"]:
                errors.append(
                    f"Field '{field}' value {value} exceeds maximum {field_schema['maximum']}"
                )

        # Check for array constraints
        if expected_type == "array" and isinstance(value, list):
            if "minItems" in field_schema and len(value) < field_schema["minItems"]:
                errors.append(
                    f"Field '{field}' has {len(value)} items, less than minItems {field_schema['minItems']}"
                )
            if "maxItems" in field_schema and len(value) > field_schema["maxItems"]:
                errors.append(
                    f"Field '{field}' has {len(value)} items, exceeds maxItems {field_schema['maxItems']}"
                )

    return errors


def validate_jsonl_against_schema(
    file_path: str, schema_name: str, max_records: Optional[int] = None
) -> Tuple[int, int, List[str]]:
    """
    Validate a JSONL file against a named schema.

    Args:
        file_path: Path to the JSONL file.
        schema_name: Name of the schema to use (without extension).
        max_records: Maximum number of records to validate (None for all).

    Returns:
        Tuple of (valid_count, invalid_count, list of error messages).
    """
    schema = load_schema(schema_name)
    if not schema:
        return 0, 0, [f"Schema '{schema_name}' not found"]

    errors = []
    valid_count = 0
    invalid_count = 0

    if not os.path.exists(file_path):
        return 0, 0, [f"File not found: {file_path}"]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    record_errors = validate_record_against_schema(record, schema)
                    if record_errors:
                        invalid_count += 1
                        for err in record_errors:
                            errors.append(f"Line {line_num}: {err}")
                    else:
                        valid_count += 1
                except json.JSONDecodeError as e:
                    invalid_count += 1
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")

                if max_records and line_num >= max_records:
                    break

    except Exception as e:
        return 0, 0, [f"Error reading file: {str(e)}"]

    return valid_count, invalid_count, errors


def validate_parquet_against_schema(
    file_path: str, schema_name: str, max_records: Optional[int] = None
) -> Tuple[int, int, List[str]]:
    """
    Validate a Parquet file against a named schema.

    Args:
        file_path: Path to the Parquet file.
        schema_name: Name of the schema to use.
        max_records: Maximum number of records to validate.

    Returns:
        Tuple of (valid_count, invalid_count, list of error messages).
    """
    # Note: Parquet validation requires pyarrow or pandas
    # This is a simplified implementation that checks basic structure
    try:
        import pandas as pd
    except ImportError:
        return 0, 0, ["pyarrow or pandas required for Parquet validation"]

    schema = load_schema(schema_name)
    if not schema:
        return 0, 0, [f"Schema '{schema_name}' not found"]

    errors = []
    valid_count = 0
    invalid_count = 0

    if not os.path.exists(file_path):
        return 0, 0, [f"File not found: {file_path}"]

    try:
        df = pd.read_parquet(file_path)
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required columns
        for field in required:
            if field not in df.columns:
                errors.append(f"Missing required column: {field}")

        # Sample validation
        sample_size = max_records if max_records else len(df)
        sample_df = df.head(sample_size)

        for idx, row in sample_df.iterrows():
            record = row.to_dict()
            record_errors = validate_record_against_schema(record, schema)
            if record_errors:
                invalid_count += 1
                for err in record_errors:
                    errors.append(f"Row {idx}: {err}")
            else:
                valid_count += 1

    except Exception as e:
        return 0, 0, [f"Error reading Parquet file: {str(e)}"]

    return valid_count, invalid_count, errors


def validate_dataset_artifact(
    artifact_path: str, schema_name: str, artifact_type: str = "jsonl"
) -> Dict[str, Any]:
    """
    Validate a dataset artifact and return a detailed report.

    Args:
        artifact_path: Path to the artifact.
        schema_name: Name of the schema to validate against.
        artifact_type: Type of artifact ('jsonl' or 'parquet').

    Returns:
        Dictionary containing validation results.
    """
    if not os.path.exists(artifact_path):
        return {
            "status": "FAILED",
            "message": f"Artifact not found: {artifact_path}",
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [f"File not found: {artifact_path}"],
        }

    if artifact_type == "jsonl":
        valid_count, invalid_count, errors = validate_jsonl_against_schema(
            artifact_path, schema_name
        )
    elif artifact_type == "parquet":
        valid_count, invalid_count, errors = validate_parquet_against_schema(
            artifact_path, schema_name
        )
    else:
        return {
            "status": "FAILED",
            "message": f"Unsupported artifact type: {artifact_type}",
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [f"Unsupported artifact type: {artifact_type}"],
        }

    total_count = valid_count + invalid_count
    status = "PASSED" if invalid_count == 0 and total_count > 0 else "FAILED"

    return {
        "status": status,
        "message": f"Validated {total_count} records, {invalid_count} errors",
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total_count": total_count,
        "errors": errors[:100],  # Limit error list
        "artifact_path": artifact_path,
        "schema_name": schema_name,
    }


def validate_all_curated_artifacts() -> Dict[str, Any]:
    """
    Validate all curated artifacts against their respective schemas.

    Returns:
        Dictionary containing validation results for all artifacts.
    """
    results = {}
    artifacts = [
        ("data/curated/hard_subset.jsonl", "dataset_schema", "jsonl"),
        ("data/curated/non_hard_subset.jsonl", "dataset_schema", "jsonl"),
        ("data/curated/synthetic_issues.jsonl", "dataset_schema", "jsonl"),
        ("data/raw/swe_explore_raw.jsonl", "dataset_schema", "jsonl"),
        ("data/raw/swe_explore_with_gt.jsonl", "dataset_schema", "jsonl"),
    ]

    for artifact_rel_path, schema_name, artifact_type in artifacts:
        full_path = get_path(artifact_rel_path)
        if os.path.exists(full_path):
            results[artifact_rel_path] = validate_dataset_artifact(
                full_path, schema_name, artifact_type
            )
        else:
            results[artifact_rel_path] = {
                "status": "SKIPPED",
                "message": "File not found",
                "valid_count": 0,
                "invalid_count": 0,
                "errors": [],
            }

    return results


def generate_validation_report(results: Dict[str, Any]) -> str:
    """
    Generate a markdown validation report from results.

    Args:
        results: Dictionary of validation results.

    Returns:
        Markdown formatted report string.
    """
    lines = ["# Validation Report", ""]
    lines.append(f"Generated: {get_config_summary()['timestamp']}")
    lines.append("")

    total_valid = 0
    total_invalid = 0
    passed_count = 0
    failed_count = 0

    lines.append("## Summary")
    lines.append("")
    lines.append("| Artifact | Status | Valid | Invalid |")
    lines.append("|----------|--------|-------|---------|")

    for artifact, result in results.items():
        status = result.get("status", "UNKNOWN")
        valid = result.get("valid_count", 0)
        invalid = result.get("invalid_count", 0)

        total_valid += valid
        total_invalid += invalid

        if status == "PASSED":
            passed_count += 1
        elif status == "FAILED":
            failed_count += 1

        lines.append(f"| {artifact} | {status} | {valid} | {invalid} |")

    lines.append("")
    lines.append(f"**Total Valid Records:** {total_valid}")
    lines.append(f"**Total Invalid Records:** {total_invalid}")
    lines.append(f"**Artifacts Passed:** {passed_count}")
    lines.append(f"**Artifacts Failed:** {failed_count}")
    lines.append("")

    if failed_count > 0:
        lines.append("## Errors")
        lines.append("")
        for artifact, result in results.items():
            if result.get("status") == "FAILED" and result.get("errors"):
                lines.append(f"### {artifact}")
                for error in result["errors"][:10]:
                    lines.append(f"- {error}")
                lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point for validation script."""
    print("Starting validation of curated artifacts...")

    # Validate all curated artifacts
    results = validate_all_curated_artifacts()

    # Generate and print report
    report = generate_validation_report(results)
    print(report)

    # Save report to file
    report_path = get_path("data/curated/validation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nValidation report saved to: {report_path}")

    # Exit with appropriate code
    if any(r.get("status") == "FAILED" for r in results.values()):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
