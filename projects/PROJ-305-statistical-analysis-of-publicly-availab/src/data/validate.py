"""
Data validation module for VAERS datasets.

This module provides a command‑line interface to validate a CSV or Parquet
file against a JSON‑Schema‑style YAML contract.  It implements the API
expected by the unit tests in ``tests/unit/test_validate.py``:

* ``E_SCHEMA_MISSING`` – required column missing or schema file not found
* ``E_DATA_MISSING``   – input data file not found
* ``E_VALIDATION_FAILED`` – data frame is empty or fails basic validation
* ``load_schema`` – load a YAML schema file
* ``validate_columns`` – return a list of missing required columns
* ``validate_data`` – perform the validation, write log files and exit on
  error
* ``main`` – CLI entry point (``python -m src.data.validate``)

The CLI writes ``logs/validate_pass.txt`` on success and
``logs/validate_fail.txt`` on failure, then exits with the appropriate
return code.
"""

import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any

import pandas as pd
import yaml

# ---------------------------------------------------------------------------
# Exit codes (aligned with the test suite)
# ---------------------------------------------------------------------------
E_SCHEMA_MISSING = 1          # Schema file missing or required column absent
E_DATA_MISSING = 2            # Input data file not found
E_VALIDATION_FAILED = 3       # Data empty or other validation problem

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _write_log_file(passed: bool, details: str | None = None) -> None:
    """Write a tiny log indicating success or failure."""
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

    Parameters
    ----------
    schema_path: str or Path
        Path to the YAML file.

    Returns
    -------
    dict
        Parsed schema dictionary.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file cannot be parsed.
    """
    path = Path(schema_path)
    if not path.exists():
        log.error(f"Schema file not found: {path}")
        raise FileNotFoundError(str(path))

    with path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise yaml.YAMLError("Schema does not contain a mapping.")
    return schema

def _required_columns_from_schema(schema: Dict[str, Any]) -> Set[str]:
    """
    Extract the list of required columns from the schema.

    The spec uses either a ``required`` list (JSON‑Schema) or a
    ``required_columns`` list (the custom test schema).
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
    if not path.exists():
        log.error(f"Data file not found: {path}")
        raise FileNotFoundError(str(path))

    try:
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, dtype=str)
    except Exception as exc:
        log.error(f"Failed to read data file {path}: {exc}")
        raise

    return df

def validate_data(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate *df* against *schema*.

    - Checks that all required columns are present.
    - Checks that the DataFrame is not empty.
    - Writes log files and exits with the appropriate ``sys.exit`` code
      on failure.

    Returns
    -------
    bool
        ``True`` if validation succeeds (the function does **not**
        terminate the interpreter in that case).
    """
    required_cols = list(_required_columns_from_schema(schema))
    log.info(f"Required columns according to schema: {sorted(required_cols)}")

    # 1. Missing required columns
    missing = validate_columns(df, required_cols)
    if missing:
        msg = f"Missing required columns: {missing}"
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        sys.exit(E_SCHEMA_MISSING)

    # 2. Empty dataframe
    if df.empty:
        msg = "Dataframe is empty."
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        sys.exit(E_VALIDATION_FAILED)

    # If we reach here, validation succeeded
    _write_log_file(passed=True)
    log.info("Data validation successful.")
    return True

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """
    CLI interface.

    Usage:
        python -m src.data.validate --data <path> [--schema <path>]

    The test suite uses the long options ``--data`` and ``--schema``.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a VAERS CSV/Parquet file against a dataset schema."
    )
    parser.add_argument(
        "--data",
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
        df = _load_data(args.data)
    except FileNotFoundError:
        sys.exit(E_DATA_MISSING)

    # Perform validation – this function exits on error
    validate_data(df, schema)
    # If we get here, validation succeeded; exit 0
    sys.exit(0)

if __name__ == "__main__":
    main()
