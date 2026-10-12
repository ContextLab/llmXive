"""
Simple validator wrapper that uses jsonschema for JSON files and pandas for CSV.
Provides a CLI entry point so it can be invoked as:
    python -m code.validators --validate <data_path> --schema <schema_path>
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List

import pandas as pd
from jsonschema import Draft7Validator

log = logging.getLogger(__name__)

def validate_file(data_path: str, schema_path: str) -> bool:
    """Validate a CSV or JSON file against the supplied schema."""
    data_file = Path(data_path)
    schema_file = Path(schema_path)

    if not data_file.exists():
        log.error(f"Data file missing: {data_path}")
        return False
    if not schema_file.exists():
        log.error(f"Schema file missing: {schema_path}")
        return False

    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    if data_file.suffix.lower() == ".json":
        with open(data_file, "r", encoding="utf-8") as f:
            instance = json.load(f)
        validator = Draft7Validator(schema)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
        if errors:
            for e in errors:
                log.error(f"Validation error: {e.message}")
            return False
        return True

    if data_file.suffix.lower() == ".csv":
        df = pd.read_csv(data_file)
        required: List[str] = schema.get("required", [])
        for col in required:
            if col not in df.columns:
                log.error(f"Missing required column '{col}'")
                return False
        # Additional type checks could be added here if the schema defines them
        return True

    log.error(f"Unsupported file type: {data_file.suffix}")
    return False

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a data file (CSV/JSON) against a JSON Schema."
    )
    parser.add_argument(
        "--validate",
        nargs=2,
        metavar=("DATA_PATH", "SCHEMA_PATH"),
        help="Path to the data file and the JSON schema file.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress logging output except for errors.",
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_args()
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.validate:
        log.error("No validation arguments supplied.")
        return 1

    data_path, schema_path = args.validate
    success = validate_file(data_path, schema_path)
    return 0 if success else 1

if __name__ == "__main__":
    raise SystemExit(main())
