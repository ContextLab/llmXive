"""
Validation utilities for the project.

Two modes are supported via the CLI:

1. Data-vs-schema validation (a pair of paths):
       python code/validators.py --validate <data_file> <schema_file>
   JSON and YAML schema files are supported; data files may be JSON or CSV.

2. Schema self-validation (a single path, or several):
       python code/validators.py --validate contracts/schema_a.yaml [more...]
   Each file is loaded and checked to be a valid JSON Schema (Draft 7).
   This is the mode used to verify that every contract in
   ``specs/001-predicting-molecular-conductivity-from-g/contracts/``
   is itself a well-formed schema (exit 0 for all).
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Union

import pandas as pd
import yaml
from jsonschema import Draft7Validator

log = logging.getLogger(__name__)


def _load_document(path: Path) -> Union[dict, list]:
    """Load a JSON or YAML document from disk."""
    with open(path, "r", encoding="utf-8") as f:
        if path.suffix.lower() in (".yaml", ".yml"):
            return yaml.safe_load(f)
        return json.load(f)


def check_schema_file(schema_path: str) -> bool:
    """Validate that a file contains a well-formed JSON Schema (Draft 7)."""
    schema_file = Path(schema_path)
    if not schema_file.exists():
        log.error(f"Schema file missing: {schema_path}")
        return False
    try:
        schema = _load_document(schema_file)
    except Exception as exc:
        log.error(f"Failed to parse schema '{schema_path}': {exc}")
        return False
    try:
        Draft7Validator.check_schema(schema)
    except Exception as exc:
        log.error(f"Invalid JSON Schema in '{schema_path}': {exc}")
        return False
    log.info(f"Schema OK: {schema_path}")
    return True


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

    try:
        schema = _load_document(schema_file)
    except Exception as exc:
        log.error(f"Failed to parse schema '{schema_path}': {exc}")
        return False

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
        required: List[str] = schema.get("required", []) or []
        for col in required:
            if col not in df.columns:
                log.error(f"Missing required column '{col}'")
                return False
        return True

    log.error(f"Unsupported file type: {data_file.suffix}")
    return False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a data file (CSV/JSON) against a JSON Schema, "
        "or self-check schema files."
    )
    parser.add_argument(
        "--validate",
        nargs="+",
        metavar="PATH",
        help="Either one or more schema files (self-check), or exactly two "
        "paths: <data_file> <schema_file>.",
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

    paths = args.validate
    if len(paths) == 1:
        return 0 if check_schema_file(paths[0]) else 1
    if len(paths) == 2:
        data_path, schema_path = paths
        return 0 if validate_file(data_path, schema_path) else 1
    # More than two paths: treat every path as a schema file to self-check.
    ok = all(check_schema_file(p) for p in paths)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
