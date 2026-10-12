"""
Simple validator wrapper that uses jsonschema for JSON files and pandas for CSV.
"""

import json
import logging
from pathlib import Path

import pandas as pd
from jsonschema import Draft7Validator, RefResolver

log = logging.getLogger(__name__)

def validate_file(data_path: str, schema_path: str) -> bool:
    """Validate a CSV or JSON file against the supplied schema."""
    data_file = Path(data_path)
    schema_file = Path(schema_path)

    if not data_file.exists() or not schema_file.exists():
        log.error("Data or schema file missing.")
        return False

    with open(schema_file) as f:
        schema = json.load(f)

    if data_file.suffix.lower() == ".json":
        with open(data_file) as f:
            instance = json.load(f)
        validator = Draft7Validator(schema)
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
        if errors:
            for e in errors:
                log.error(f"Validation error: {e.message}")
            return False
        return True
    elif data_file.suffix.lower() == ".csv":
        df = pd.read_csv(data_file)
        # Very simple column‑type check based on schema properties
        required = schema.get("required", [])
        for col in required:
            if col not in df.columns:
                log.error(f"Missing required column '{col}'")
                return False
        return True
    else:
        log.error(f"Unsupported file type: {data_file.suffix}")
        return False
