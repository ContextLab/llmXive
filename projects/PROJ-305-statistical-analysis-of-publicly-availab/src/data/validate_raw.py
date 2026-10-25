"""
Raw VAERS dataset validation script (T003).

Provides a command-line interface:
    python -m src.data.validate_raw --schema <schema_path> --input <file>

The CLI writes `logs/validate_raw_pass.txt` on success and
`logs/validate_raw_fail.txt` on failure, then exits with:
    0 – validation succeeded
    1 – any failure (schema missing, data missing, or validation failed)
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml
import jsonschema
from jsonschema import validate, ValidationError, SchemaError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _write_log_file(passed: bool, details: str | None = None) -> None:
    """Create `logs/validate_raw_pass.txt` or `logs/validate_raw_fail.txt`."""
    logs_dir = paths.logs()
    logs_dir.mkdir(parents=True, exist_ok=True)
    if passed:
        (logs_dir / "validate_raw_pass.txt").write_text("PASS\n", encoding="utf-8")
    else:
        text = "FAIL\n"
        if details:
            text += f"{details}\n"
        (logs_dir / "validate_raw_fail.txt").write_text(text, encoding="utf-8")

def validate_raw_dataset(input_path: Path, schema_path: Path) -> bool:
    """
    Validates a parquet file against a JSON-Schema.
    Since the dataset is large, it validates the column structure 
    and a sample of the records.
    """
    try:
        # 1. Load Schema
        if not schema_path.is_file():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a YAML mapping.")

        # 2. Load Data
        if not input_path.is_file():
            raise FileNotFoundError(f"Input data file not found: {input_path}")
        
        # Load a sample to validate types/formats without blowing up memory
        # We read only the first 1000 rows for schema validation
        df_sample = pd.read_parquet(input_path).head(1000)
        
        if df_sample.empty:
            raise ValueError("The input dataset is empty.")

        # 3. Validate using jsonschema
        # Convert DataFrame sample to list of dicts for jsonschema
        records = df_sample.to_dict(orient="records")
        
        for i, record in enumerate(records):
            try:
                validate(instance=record, schema=schema)
            except ValidationError as ve:
                log.error("Validation error at row %d: %s", i, ve.message)
                return False
        
        log.info("Successfully validated sample of %d records against schema.", len(records))
        return True

    except SchemaError as se:
        log.error("Invalid JSON-Schema provided: %s", se.message)
        return False
    except Exception as e:
        log.error("Validation process encountered an error: %s", e)
        return False

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate raw VAERS parquet file against a JSON-Schema."
    )
    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Path to the JSON-Schema YAML file.",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the raw VAERS parquet (or CSV) file to validate.",
    )
    args = parser.parse_args()

    schema_path = Path(args.schema)
    input_path = Path(args.input)

    if validate_raw_dataset(input_path, schema_path):
        _write_log_file(passed=True)
        sys.exit(0)
    else:
        _write_log_file(passed=False, details="Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
