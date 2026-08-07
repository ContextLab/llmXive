"""
Schema Validation Helper for llmXive.

Validates JSONL/Parquet files against the YAML schemas defined in
specs/.../contracts/.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import yaml

from config import get_path, DATA_RAW, DATA_CURATED, DATA_RESULTS
from utils.schemas import get_schema_path, load_schema


def validate_field_type(value: Any, expected_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value matches the expected JSON Schema type.
    Returns (is_valid, error_message).
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
        return True, None  # Unknown type, skip strict check

    expected_python_type = type_map[expected_type]

    # Special case for integer/number: if it's a bool, it's not a number
    if expected_type == "integer" and isinstance(value, bool):
        return False, f"Expected integer, got bool"
    if expected_type == "number" and isinstance(value, bool):
        return False, f"Expected number, got bool"

    if not isinstance(value, expected_python_type):
        return False, f"Expected {expected_type}, got {type(value).__name__}"

    return True, None


def validate_record_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record (dict) against a JSON Schema definition.
    Returns a list of error messages.
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check types for present fields
    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            field_type = field_schema.get("type")
            if field_type:
                is_valid, err = validate_field_type(value, field_type)
                if not is_valid:
                    errors.append(f"Field '{field}': {err}")

    return errors


def validate_jsonl_against_schema(file_path: Path, schema_name: str) -> Tuple[int, int, List[str]]:
    """
    Validate a JSONL file against a named schema.
    Returns (valid_count, total_count, list_of_errors).
    """
    schema = load_schema(schema_name)
    if not schema:
        raise FileNotFoundError(f"Schema '{schema_name}' not found.")

    valid_count = 0
    total_count = 0
    all_errors = []

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            total_count += 1
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"Line {line_num}: JSON decode error: {e}")
                continue

            record_errors = validate_record_against_schema(record, schema)
            if record_errors:
                for err in record_errors:
                    all_errors.append(f"Line {line_num}: {err}")
            else:
                valid_count += 1

    return valid_count, total_count, all_errors


def validate_parquet_against_schema(file_path: Path, schema_name: str) -> Tuple[int, int, List[str]]:
    """
    Validate a Parquet file against a named schema.
    Note: This implementation assumes 'pyarrow' and 'pandas' are available.
    Returns (valid_count, total_count, list_of_errors).
    """
    try:
        import pandas as pd
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError("pyarrow and pandas are required to validate Parquet files.")

    schema = load_schema(schema_name)
    if not schema:
        raise FileNotFoundError(f"Schema '{schema_name}' not found.")

    try:
        table = pq.read_table(str(file_path))
        df = table.to_pandas()
    except Exception as e:
        raise RuntimeError(f"Failed to read Parquet file {file_path}: {e}")

    valid_count = 0
    total_count = len(df)
    all_errors = []

    # Convert schema properties to a simpler check for columns
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check columns
    missing_cols = set(required_fields) - set(df.columns)
    if missing_cols:
        all_errors.append(f"Missing columns: {missing_cols}")
        return 0, total_count, all_errors

    # Validate types row by row (simplified for Parquet)
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        record_errors = validate_record_against_schema(row_dict, schema)
        if record_errors:
            for err in record_errors:
                all_errors.append(f"Row {idx}: {err}")
        else:
            valid_count += 1

    return valid_count, total_count, all_errors


def validate_dataset_artifact(file_path: Path, schema_name: str) -> Dict[str, Any]:
    """
    Validate a dataset artifact (JSONL or Parquet) and return a summary.
    """
    suffix = file_path.suffix.lower()

    try:
        if suffix == ".jsonl":
            valid, total, errors = validate_jsonl_against_schema(file_path, schema_name)
        elif suffix == ".parquet":
            valid, total, errors = validate_parquet_against_schema(file_path, schema_name)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
    except Exception as e:
        return {
            "file": str(file_path),
            "schema": schema_name,
            "status": "ERROR",
            "error": str(e),
            "valid_count": 0,
            "total_count": 0,
            "errors": []
        }

    status = "PASS" if len(errors) == 0 else "FAIL"
    return {
        "file": str(file_path),
        "schema": schema_name,
        "status": status,
        "valid_count": valid,
        "total_count": total,
        "error_count": len(errors),
        "errors": errors[:10]  # Limit error list for report
    }


def validate_all_curated_artifacts() -> List[Dict[str, Any]]:
    """
    Validate all curated artifacts against their respective schemas.
    Returns a list of validation results.
    """
    results = []
    curated_dir = Path(DATA_CURATED)

    if not curated_dir.exists():
        return [{"status": "SKIP", "reason": "Curated directory not found"}]

    # Mapping of file patterns to schema names (based on T004 contracts)
    # Adjust these keys if the actual filenames differ
    file_schema_map = {
        "hard_subset.jsonl": "dataset_schema",
        "synthetic_issues.jsonl": "dataset_schema",
        "ground_truth.jsonl": "dataset_schema",
        "agent_logs.jsonl": "agent_log_schema",
        "results.jsonl": "result_schema",
    }

    for filename, schema_name in file_schema_map.items():
        file_path = curated_dir / filename
        if file_path.exists():
            result = validate_dataset_artifact(file_path, schema_name)
            results.append(result)
        else:
            # Only skip if the file is expected but missing, or log warning
            # For now, we just skip missing optional files
            pass

    return results


def generate_validation_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a text report of validation results.
    """
    lines = [
        "# Schema Validation Report",
        f"Generated: {Path(output_path).parent.name}",
        "",
    ]

    passed = 0
    failed = 0
    errors = 0

    for res in results:
        status = res.get("status", "UNKNOWN")
        if status == "PASS":
            passed += 1
        elif status == "FAIL":
            failed += 1
        elif status == "ERROR":
            errors += 1

        lines.append(f"## {res.get('file', 'Unknown')}")
        lines.append(f"- Schema: {res.get('schema', 'N/A')}")
        lines.append(f"- Status: {status}")
        if "valid_count" in res:
            lines.append(f"- Valid Records: {res['valid_count']}/{res['total_count']}")
        if res.get("error"):
            lines.append(f"- Error: {res['error']}")
        if res.get("errors"):
            lines.append("- Errors:")
            for err in res["errors"]:
                lines.append(f"  - {err}")
        lines.append("")

    lines.append("## Summary")
    lines.append(f"- Passed: {passed}")
    lines.append(f"- Failed: {failed}")
    lines.append(f"- Errors: {errors}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    """
    CLI entry point for validation.
    Usage: python -m utils.validation [--input <path>] [--schema <name>]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate data artifacts against schemas.")
    parser.add_argument("--input", type=str, help="Path to input file (JSONL or Parquet).")
    parser.add_argument("--schema", type=str, help="Schema name (e.g., dataset_schema).")
    parser.add_argument("--all", action="store_true", help="Validate all curated artifacts.")
    parser.add_argument("--output", type=str, help="Output path for report (if --all).")

    args = parser.parse_args()

    if args.all:
        results = validate_all_curated_artifacts()
        if not results:
            print("No artifacts found to validate.")
            return
        output_path = Path(args.output) if args.output else Path(DATA_RESULTS) / "validation_report.txt"
        generate_validation_report(results, output_path)
        print(f"Validation report written to {output_path}")
        # Exit with error if any failed
        if any(r.get("status") in ["FAIL", "ERROR"] for r in results):
            sys.exit(1)
    elif args.input and args.schema:
        file_path = Path(args.input)
        try:
            valid, total, errors = validate_jsonl_against_schema(file_path, args.schema)
            if errors:
                print(f"Validation FAILED for {file_path}")
                for err in errors[:5]:
                    print(f"  {err}")
                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more errors")
                sys.exit(1)
            else:
                print(f"Validation PASSED for {file_path}: {valid}/{total} records valid.")
        except Exception as e:
            print(f"Error validating {file_path}: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()