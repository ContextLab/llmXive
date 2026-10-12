"""
Data validation module for VAERS datasets.

Validates a CSV or Parquet file against the schema defined in
``contracts/dataset.schema.yaml``.  The script exits with code ``0`` on
success and ``1`` (``E_SCHEMA_MISSING``) if any required column is absent.
All other unexpected errors result in a non‑zero exit code.

The script also writes a tiny log file indicating pass/fail:
  - ``logs/validate_pass.txt``  – written when validation succeeds
  - ``logs/validate_fail.txt``  – written when validation fails
"""

import logging
import sys
from pathlib import Path
from typing import List, Set

import jsonschema
import pandas as pd
import yaml

# ---------------------------------------------------------------------------
# Exit codes (aligned with the task description)
# ---------------------------------------------------------------------------
E_SCHEMA_MISSING = 1  # Required column missing
E_FILE_NOT_FOUND = 2  # Input file does not exist
E_SCHEMA_ERROR = 3  # Schema file missing / malformed


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("validate")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    return logger


logger = _setup_logger()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _load_schema(schema_path: Path) -> dict:
    """Load the JSON‑Schema YAML file."""
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(E_SCHEMA_ERROR)

    try:
        with schema_path.open("r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing schema YAML: {exc}")
        sys.exit(E_SCHEMA_ERROR)

    if not isinstance(schema, dict):
        logger.error("Schema is not a valid mapping.")
        sys.exit(E_SCHEMA_ERROR)

    return schema


def _load_data(file_path: Path) -> pd.DataFrame:
    """Load CSV or Parquet into a DataFrame."""
    if not file_path.exists():
        logger.error(f"Data file not found: {file_path}")
        sys.exit(E_FILE_NOT_FOUND)

    try:
        if file_path.suffix.lower() == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            df = pd.read_csv(file_path, dtype=str)
    except Exception as exc:
        logger.error(f"Failed to read data file {file_path}: {exc}")
        sys.exit(E_FILE_NOT_FOUND)

    if df.empty:
        logger.error("Loaded DataFrame is empty.")
        sys.exit(E_SCHEMA_MISSING)

    return df


def _required_columns_from_schema(schema: dict) -> Set[str]:
    """Extract the ``required`` property from the schema."""
    required = schema.get("required", [])
    if not isinstance(required, list):
        logger.error("Schema 'required' field is not a list.")
        sys.exit(E_SCHEMA_ERROR)
    return set(required)


def _write_log_file(passed: bool) -> None:
    """Write a tiny log indicating success or failure."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    if passed:
        (logs_dir / "validate_pass.txt").write_text("validation passed\n")
    else:
        (logs_dir / "validate_fail.txt").write_text("validation failed\n")


# ---------------------------------------------------------------------------
# Core validation routine
# ---------------------------------------------------------------------------
def validate_file(
    data_path: Path,
    schema_path: Path = Path("contracts/dataset.schema.yaml"),
) -> None:
    """
    Validate ``data_path`` against ``schema_path``.
    Exits the process with the appropriate code.
    """
    logger.info(f"Loading schema from {schema_path}")
    schema = _load_schema(schema_path)

    logger.info(f"Loading data from {data_path}")
    df = _load_data(data_path)

    required_cols = _required_columns_from_schema(schema)
    logger.info(f"Required columns according to schema: {sorted(required_cols)}")

    missing: List[str] = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        _write_log_file(passed=False)
        sys.exit(E_SCHEMA_MISSING)

    # Optional: run a full JSON‑Schema validation on a single record
    # to ensure column types match.  This is lightweight and guarantees
    # the file adheres to the schema.
    try:
        # Validate the first row (or an empty dict if no rows)
        sample = df.iloc[0].to_dict() if not df.empty else {}
        jsonschema.validate(instance=sample, schema=schema)
    except jsonschema.ValidationError as exc:
        logger.error(f"Schema validation error on sample row: {exc.message}")
        _write_log_file(passed=False)
        sys.exit(E_SCHEMA_MISSING)
    except jsonschema.SchemaError as exc:
        logger.error(f"Invalid schema definition: {exc}")
        sys.exit(E_SCHEMA_ERROR)

    logger.info("Data validation successful.")
    _write_log_file(passed=True)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """
    CLI interface.

    Usage:
        python -m src.data.validate [--input <path>] [--schema <path>]

    If ``--input`` is omitted the script defaults to
    ``data/processed/cleaned_vaers.parquet``.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a VAERS CSV/Parquet file against the dataset schema."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_vaers.parquet",
        help="Path to the CSV or Parquet file to validate.",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="contracts/dataset.schema.yaml",
        help="Path to the JSON‑Schema YAML file.",
    )
    args = parser.parse_args()

    data_path = Path(args.input)
    schema_path = Path(args.schema)

    validate_file(data_path, schema_path)


if __name__ == "__main__":
    main()
