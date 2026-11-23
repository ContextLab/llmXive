"""
Schema Validation Helper for llmXive.

This module provides utilities to validate JSONL/Parquet files against
the YAML schemas defined in specs/.../contracts/.

It ONLY validates file structure and schema compliance. It does NOT
filter data, generate synthetic issues, implement agents, or compute metrics.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

from config import get_path


def get_schema_path(schema_name: str) -> Path:
    """
    Resolve the path to a schema file in the contracts directory.

    Args:
        schema_name: The name of the schema file (e.g., 'dataset_schema.yaml').

    Returns:
        Path to the schema file.

    Raises:
        FileNotFoundError: If the schema file does not exist.
    """
    contracts_dir = get_path("contracts_dir")
    schema_file = contracts_dir / schema_name
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    return schema_file


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.

    Args:
        schema_name: The name of the schema file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    schema_path = get_schema_path(schema_name)
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type string.

    Supported types: string, integer, number, boolean, array, object, null.

    Args:
        value: The value to check.
        expected_type: The expected type as a string.

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
        # Unknown type, assume valid or log warning
        return True

    expected_python_type = type_map[expected_type]

    # Special case: bool is a subclass of int in Python, so check bool first
    if expected_type == "integer" and isinstance(value, bool):
        return False

    return isinstance(value, expected_python_type)


def validate_record_against_schema(
    record: Dict[str, Any], schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate a single record against a schema definition.

    Args:
        record: The data record to validate.
        schema: The schema definition dictionary.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check field types and presence
    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get("type")

            if expected_type:
                if not validate_field_type(value, expected_type):
                    errors.append(
                        f"Field '{field}' has incorrect type. "
                        f"Expected: {expected_type}, Got: {type(value).__name__}"
                    )

            # Check for nested objects (simple recursive check)
            if expected_type == "object" and isinstance(value, dict):
                nested_props = field_schema.get("properties", {})
                # Only validate top-level nested keys if defined
                for nested_key, nested_val in value.items():
                    if nested_key in nested_props:
                        nested_type = nested_props[nested_key].get("type")
                        if nested_type and not validate_field_type(nested_val, nested_type):
                            errors.append(
                                f"Nested field '{field}.{nested_key}' has incorrect type. "
                                f"Expected: {nested_type}, Got: {type(nested_val).__name__}"
                            )

        else:
            # Optional: warn about unknown fields? For now, we allow extra fields.
            pass

    return len(errors) == 0, errors


def validate_jsonl_against_schema(
    file_path: str, schema_name: str
) -> Tuple[bool, List[str], int]:
    """
    Validate a JSONL file against a schema.

    Args:
        file_path: Path to the JSONL file.
        schema_name: Name of the schema file in contracts.

    Returns:
        Tuple of (all_valid, list_of_all_errors, record_count).
    """
    schema = load_schema(schema_name)
    errors = []
    record_count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"Line {line_num}: Invalid JSON - {e}")
                continue

            record_count += 1
            is_valid, record_errors = validate_record_against_schema(record, schema)
            if not is_valid:
                for err in record_errors:
                    errors.append(f"Line {line_num}: {err}")

    return len(errors) == 0, errors, record_count


def validate_parquet_against_schema(
    file_path: str, schema_name: str
) -> Tuple[bool, List[str], int]:
    """
    Validate a Parquet file against a schema.
    Note: This is a placeholder implementation as parquet support requires
    pyarrow/pandas which might not be in the base requirements yet.
    If parquet files are needed, ensure pyarrow is installed.

    Args:
        file_path: Path to the Parquet file.
        schema_name: Name of the schema file in contracts.

    Returns:
        Tuple of (all_valid, list_of_all_errors, record_count).
    """
    try:
        import pandas as pd
    except ImportError:
        return False, ["pandas is required to validate Parquet files"], 0

    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        return False, [f"Failed to read Parquet file: {e}"], 0

    schema = load_schema(schema_name)
    errors = []
    record_count = len(df)

    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")

    # Check types (basic check)
    for col in df.columns:
        if col in properties:
            expected_type = properties[col].get("type")
            if expected_type:
                # Map schema types to pandas dtypes roughly
                if expected_type == "string" and not df[col].dtype == "object":
                    # Pandas strings are often object or string dtype
                    if not str(df[col].dtype).startswith("str"):
                        errors.append(f"Column '{col}' type mismatch: {df[col].dtype}")
                elif expected_type == "integer" and not "int" in str(df[col].dtype):
                    errors.append(f"Column '{col}' type mismatch: {df[col].dtype}")
                elif expected_type == "number" and not ("int" in str(df[col].dtype) or "float" in str(df[col].dtype)):
                    errors.append(f"Column '{col}' type mismatch: {df[col].dtype}")

    return len(errors) == 0, errors, record_count


def validate_dataset_artifact(file_path: str, schema_name: str) -> bool:
    """
    Validate a dataset artifact (JSONL or Parquet) against a schema.

    Args:
        file_path: Path to the data file.
        schema_name: Name of the schema file.

    Returns:
        True if validation passes, False otherwise (logs errors).
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return False

    if path.suffix == ".jsonl":
        valid, errors, count = validate_jsonl_against_schema(str(path), schema_name)
    elif path.suffix == ".parquet":
        valid, errors, count = validate_parquet_against_schema(str(path), schema_name)
    else:
        print(f"Error: Unsupported file format: {path.suffix}", file=sys.stderr)
        return False

    if not valid:
        print(f"Validation failed for {file_path} ({count} records):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return False

    print(f"Validation passed for {file_path} ({count} records).")
    return True


def validate_all_curated_artifacts() -> bool:
    """
    Validate all curated artifacts against their respective schemas.
    This is a convenience function to run the full validation suite.

    Returns:
        True if all validations pass, False otherwise.
    """
    # Define mappings of file patterns to schema names
    # These should match the schemas created in T004
    artifacts = [
        ("data/curated/hard_subset.jsonl", "dataset_schema.yaml"),
        ("data/curated/synthetic_issues.jsonl", "dataset_schema.yaml"),
        ("data/results/iterative_logs.jsonl", "agent_log_schema.yaml"),
        ("data/results/baseline_onshot_logs.jsonl", "agent_log_schema.yaml"),
        ("data/results/final_metrics.json", "result_schema.yaml"), # Note: JSON vs JSONL
    ]

    all_passed = True

    for file_pattern, schema_name in artifacts:
        full_path = get_path("project_root") / file_pattern
        if full_path.exists():
            # For JSON files (like final_metrics), we might need a different validator
            # For now, we assume the schema structure is compatible or skip if extension mismatch
            if full_path.suffix == ".json" and "result_schema" in schema_name:
                # Special handling for single JSON object vs JSONL
                # Load and validate top level
                try:
                    with open(full_path, "r") as f:
                        data = json.load(f)
                    schema = load_schema(schema_name)
                    is_valid, errors = validate_record_against_schema(data, schema)
                    if not is_valid:
                        print(f"Validation failed for {file_pattern}: {errors}", file=sys.stderr)
                        all_passed = False
                    else:
                        print(f"Validation passed for {file_pattern}.")
                except Exception as e:
                    print(f"Error validating {file_pattern}: {e}", file=sys.stderr)
                    all_passed = False
            else:
                if not validate_dataset_artifact(str(full_path), schema_name):
                    all_passed = False
        else:
            print(f"Warning: Artifact not found, skipping: {file_pattern}")

    return all_passed


def generate_validation_report(output_path: str) -> bool:
    """
    Generate a markdown validation report for all curated artifacts.

    Args:
        output_path: Path to write the report.

    Returns:
        True if report generation succeeds.
    """
    report_lines = [
        "# Validation Report",
        f"Generated: {__import__('datetime').datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
    ]

    artifacts = [
        ("data/curated/hard_subset.jsonl", "dataset_schema.yaml"),
        ("data/curated/synthetic_issues.jsonl", "dataset_schema.yaml"),
        ("data/results/iterative_logs.jsonl", "agent_log_schema.yaml"),
    ]

    all_passed = True
    for file_pattern, schema_name in artifacts:
        full_path = get_path("project_root") / file_pattern
        if full_path.exists():
            valid, errors, count = validate_jsonl_against_schema(str(full_path), schema_name)
            status = "PASS" if valid else "FAIL"
            if not valid:
                all_passed = False
            report_lines.append(f"### {file_pattern}")
            report_lines.append(f"- **Status**: {status}")
            report_lines.append(f"- **Records**: {count}")
            if errors:
                report_lines.append("- **Errors**:")
                for err in errors[:10]: # Limit errors in report
                    report_lines.append(f"  - {err}")
                if len(errors) > 10:
                    report_lines.append(f"  - ... and {len(errors) - 10} more")
            report_lines.append("")
        else:
            report_lines.append(f"### {file_pattern}")
            report_lines.append("- **Status**: SKIPPED (File not found)")
            report_lines.append("")

    report_lines.append("## Overall Status")
    report_lines.append(f"**{'PASS' if all_passed else 'FAIL'}**")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    return all_passed


def main():
    """CLI entry point for validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate data artifacts against schemas.")
    parser.add_argument(
        "--file",
        type=str,
        help="Path to the file to validate.",
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="Name of the schema file (e.g., dataset_schema.yaml).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all curated artifacts.",
    )
    parser.add_argument(
        "--report",
        type=str,
        help="Path to write a validation report.",
    )

    args = parser.parse_args()

    if args.all:
        success = validate_all_curated_artifacts()
        sys.exit(0 if success else 1)
    elif args.report:
        success = generate_validation_report(args.report)
        sys.exit(0 if success else 1)
    elif args.file and args.schema:
        success = validate_dataset_artifact(args.file, args.schema)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()