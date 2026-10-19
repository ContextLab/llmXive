"""
Data validation module for VAERS datasets (T003).

Provides a command‑line interface compatible with the test suite:

    python -m src.data.validate --input <path> [--schema <path>]

The CLI writes ``logs/validate_pass.txt`` on success and
``logs/validate_fail.txt`` on failure, then exits with the appropriate
return code.

Exit codes (aligned with the existing test expectations):
    0 – validation succeeded
    1 – schema file missing or unreadable
    2 – input data file missing
    3 – validation failure (missing required columns or empty dataframe)
"""

import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any

import pandas as pd
import yaml

# ----------------------------------------------------------------------
# Exit‑code constants
# ----------------------------------------------------------------------
E_SCHEMA_MISSING = 1          # schema file missing or unreadable
E_DATA_MISSING = 2            # input data file not found
E_VALIDATION_FAILED = 3       # missing columns, empty dataframe, etc.

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("validate")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger

log = _setup_logger()

# ----------------------------------------------------------------------
# Core helpers
# ----------------------------------------------------------------------
def _write_log_file(passed: bool, details: str | None = None) -> None:
    """Create ``logs/validate_pass.txt`` or ``logs/validate_fail.txt``."""
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    if passed:
        (logs_dir / "validate_pass.txt").write_text("PASS\n")
    else:
        text = "FAIL\n"
        if details:
            text += f"{details}\n"
        (logs_dir / "validate_fail.txt").write_text(text)

def load_schema(schema_path: str | Path) -> Dict[str, Any]:
    """
    Load a YAML schema file.

    Raises ``FileNotFoundError`` if the path does not exist.
    """
    path = Path(schema_path)
    if not path.is_file():
        log.error("Schema file not found: %s", path)
        raise FileNotFoundError(str(path))

    with path.open("r", encoding="utf-8") as f:
        try:
            schema = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            log.error("Failed to parse YAML schema: %s", exc)
            raise

    if not isinstance(schema, dict):
        raise yaml.YAMLError("Schema does not contain a mapping.")
    return schema

def _required_columns_from_schema(schema: Dict[str, Any]) -> Set[str]:
    """
    Extract required column names from the schema.  The spec may use either
    ``required`` (JSON‑Schema) or ``required_columns`` (custom) keys.
    """
    required = schema.get("required") or schema.get("required_columns") or []
    if not isinstance(required, list):
        raise ValueError("Schema 'required' field must be a list.")
    return set(required)

def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    """
    Return a list of required columns that are missing from *df*.
    """
    missing = [col for col in required_cols if col not in df.columns]
    return missing

def _load_data(data_path: str | Path) -> pd.DataFrame:
    """Load CSV or Parquet into a DataFrame."""
    path = Path(data_path)
    if not path.is_file():
        log.error("Data file not found: %s", path)
        raise FileNotFoundError(str(path))

    try:
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, dtype=str)
    except Exception as exc:
        log.error("Failed to read data file %s: %s", path, exc)
        raise

    return df

def validate_data(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Perform validation against *schema*.

    - Checks that all required columns are present.
    - Checks that the DataFrame is non‑empty.

    Writes appropriate log files and exits the interpreter with the
    correct exit code on failure.  Returns ``True`` on success.
    """
    required_cols = list(_required_columns_from_schema(schema))
    log.info("Required columns according to schema: %s", sorted(required_cols))

    # 1. Missing required columns → validation failure (code 3)
    missing = validate_columns(df, required_cols)
    if missing:
        msg = f"Missing required columns: {missing}"
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        sys.exit(E_VALIDATION_FAILED)

    # 2. Empty dataframe → validation failure (code 3)
    if df.empty:
        msg = "Dataframe is empty."
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        sys.exit(E_VALIDATION_FAILED)

    # Success
    _write_log_file(passed=True)
    log.info("Data validation successful.")
    return True

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI interface.

    Usage:
        python -m src.data.validate --input <path> [--schema <path>]

    The test suite uses the long option ``--input``; ``--schema`` defaults
    to ``contracts/dataset.schema.yaml``.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a VAERS CSV/Parquet file against a dataset schema."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the CSV or Parquet file to validate.",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="contracts/dataset.schema.yaml",
        help="Path to the JSON‑Schema YAML file.",
    )
    args = parser.parse_args()

    # Load schema (exit 1 on failure)
    try:
        schema = load_schema(args.schema)
    except FileNotFoundError:
        sys.exit(E_SCHEMA_MISSING)

    # Load data (exit 2 on failure)
    try:
        df = _load_data(args.input)
    except FileNotFoundError:
        sys.exit(E_DATA_MISSING)

    # Perform validation – this function exits on error
    validate_data(df, schema)

    # If we get here validation succeeded → exit 0
    sys.exit(0)

if __name__ == "__main__":
    main()
