#!/usr/bin/env python3
"""
Data Integrity Check Script for Constitution Principle V (Fail Fast)

This script validates data artifacts against schema contracts defined in the
contracts/ directory. It writes a detailed validation report to
data/validation_report.json.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
import pandas as pd

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a single record against a schema."""
    errors = []
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")

    # Check field types
    for field, value in record.items():
        if field in properties:
            expected_type = properties[field].get("type")
            if expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field {field} should be integer, got {type(value)}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field {field} should be number, got {type(value)}")
            elif expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field {field} should be string, got {type(value)}")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field {field} should be boolean, got {type(value)}")

    return errors

def validate_csv(csv_path: Path, schema_path: Path) -> Dict[str, Any]:
    """Validate a CSV file against a schema."""
    report = {
        "file": str(csv_path),
        "schema": str(schema_path),
        "total_records": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "errors": []
    }

    if not csv_path.exists():
        report["errors"].append("CSV file not found")
        return report

    if not schema_path.exists():
        report["errors"].append("Schema file not found")
        return report

    try:
        df = pd.read_csv(csv_path)
        schema = load_schema(schema_path)
        report["total_records"] = len(df)

        for idx, row in df.iterrows():
            record = row.to_dict()
            errors = validate_record(record, schema)
            if errors:
                report["invalid_records"] += 1
                for err in errors:
                    report["errors"].append(f"Record {idx}: {err}")
            else:
                report["valid_records"] += 1

    except Exception as e:
        report["errors"].append(f"Validation error: {str(e)}")

    return report

def main():
    project_root = Path(__file__).parent.parent
    cleaned_studies_path = project_root / "data" / "processed" / "cleaned_studies.csv"
    schema_path = project_root / "contracts" / "cleaned_study.schema.yaml"
    report_path = project_root / "data" / "validation_report.json"

    # Create data directory if it doesn't exist
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = validate_csv(cleaned_studies_path, schema_path)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Validation report saved to {report_path}")
    print(f"Total records: {report['total_records']}")
    print(f"Valid records: {report['valid_records']}")
    print(f"Invalid records: {report['invalid_records']}")

    if report["errors"]:
        print("Errors found:")
        for err in report["errors"][:10]:  # Show first 10 errors
            print(f"  - {err}")

if __name__ == "__main__":
    main()
