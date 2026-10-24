"""
validate_schema.py

Validates a CSV file of measurement records against the MeasurementRecord
definition in a JSON‑Schema file.  The script exits with status 0 if all rows
conform, otherwise it raises a jsonschema.ValidationError (which terminates
the process with a non‑zero exit code).

Usage
-----
python code/validation/validate_schema.py --schema <schema.yaml> --data <file.csv>
"""
import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft7Validator, ValidationError

def _load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON‑Schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _load_csv(data_path: Path) -> list[Dict[str, Any]]:
    """Read a CSV file into a list of dictionaries, converting numeric fields."""
    rows: list[Dict[str, Any]] = []
    with data_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            # Convert the `value` column to a float if present; leave everything else as‑is.
            row: Dict[str, Any] = dict(raw)
            if "value" in row and row["value"] != "":
                try:
                    row["value"] = float(row["value"])
                except ValueError as exc:
                    raise ValueError(
                        f"Unable to convert 'value' to float in row: {row}"
                    ) from exc
            rows.append(row)
    return rows

def _extract_measurement_schema(full_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    The top‑level schema describes the whole dataset (participants,
    measurements, compliance_logs).  For CSV validation we only need the
    ``MeasurementRecord`` definition.
    """
    try:
        return full_schema["definitions"]["MeasurementRecord"]
    except KeyError as exc:
        raise KeyError(
            "The provided schema does not contain a 'MeasurementRecord' definition."
        ) from exc

def validate_csv_against_schema(schema_path: Path, data_path: Path) -> None:
    """
    Validate each CSV row against the ``MeasurementRecord`` schema.

    Raises
    ------
    jsonschema.ValidationError
        If any row does not conform to the schema.
    """
    # 1️⃣ Load the JSON‑Schema and isolate the measurement definition.
    full_schema = _load_schema(schema_path)
    measurement_schema = _extract_measurement_schema(full_schema)

    # 2️⃣ Prepare a validator (Draft7 for compatibility with the schema version).
    validator = Draft7Validator(measurement_schema)

    # 3️⃣ Load CSV rows, performing lightweight type coercion.
    rows = _load_csv(data_path)

    # 4️⃣ Validate each row individually.  Errors are collected and reported
    #    together to make debugging easier.
    errors: list[ValidationError] = []
    for idx, row in enumerate(rows, start=1):
        # ``validator.iter_errors`` yields all errors for a single instance.
        for err in validator.iter_errors(row):
            # Attach row number for clearer messages.
            err.message = f"Row {idx}: {err.message}"
            errors.append(err)

    if errors:
        # Raise the first error; pytest (or the execution harness) will see the
        # non‑zero exit status.  Printing all errors helps the user locate problems.
        for e in errors:
            print(e.message)
        raise ValidationError(f"{len(errors)} validation error(s) found in {data_path}")

    # If we reach this point the CSV conforms to the schema.
    print(f"Validation successful: {len(rows)} rows in '{data_path}' conform to the schema.")

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate measurement CSV files against a JSON‑Schema."
    )
    parser.add_argument(
        "--schema",
        required=True,
        help="Path to the JSON‑Schema file (e.g., contracts/dataset.schema.yaml).",
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to the CSV file containing measurement records.",
    )
    return parser

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    schema_path = Path(args.schema)
    data_path = Path(args.data)

    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    if not data_path.is_file():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    try:
        validate_csv_against_schema(schema_path, data_path)
    except ValidationError as exc:
        # Propagate the exception so the process exits with a non‑zero code.
        print(f"Validation failed: {exc}")
        return 1
    except Exception as exc:
        print(f"Unexpected error during validation: {exc}")
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
