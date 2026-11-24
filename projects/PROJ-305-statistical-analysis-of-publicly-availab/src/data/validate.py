"""
Data validation module for VAERS datasets (T003).

Provides a command‑line interface:
    python -m src.data.validate --input <path> [--schema <path>]

The CLI writes `logs/validate_pass.txt` on success and
`logs/validate_fail.txt` on failure, then exits with:
    0 – validation succeeded
    1 – any failure (schema missing, data missing, or validation failed)
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import yaml
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _write_log_file(passed: bool, details: str | None = None) -> None:
    """Create `logs/validate_pass.txt` or `logs/validate_fail.txt`."""
    logs_dir = paths.logs()
    logs_dir.mkdir(parents=True, exist_ok=True)
    if passed:
        (logs_dir / "validate_pass.txt").write_text("PASS\n", encoding="utf-8")
    else:
        text = "FAIL\n"
        if details:
            text += f"{details}\n"
        (logs_dir / "validate_fail.txt").write_text(text, encoding="utf-8")

def load_schema(schema_path: str | Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.is_file():
        log.error("Schema file not found: %s", path)
        raise FileNotFoundError(str(path))

    with path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema does not contain a mapping.")
    return schema

def _get_required_columns(schema: Dict[str, Any]) -> List[str]:
    """Extract required column names from the schema."""
    required = schema.get("required") or schema.get("required_columns") or []
    if not isinstance(required, list):
        raise ValueError("Schema 'required' field must be a list.")
    return required

def _load_data(data_path: str | Path) -> pd.DataFrame:
    """Load CSV or Parquet into a DataFrame."""
    path = Path(data_path)
    if not path.is_file():
        log.error("Data file not found: %s", path)
        raise FileNotFoundError(str(path))

    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path, dtype=str)

def validate_data(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Perform validation against schema.
    - Required columns must be present.
    - Required columns must be non-null.
    - DataFrame must be non-empty.
    """
    required_cols = _get_required_columns(schema)
    log.info("Validating required columns: %s", required_cols)

    # 1. Check presence
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        msg = f"Missing required columns: {missing}"
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        return False

    # 2. Check for nulls in required columns
    null_cols = []
    for col in required_cols:
        if df[col].isnull().any():
            null_cols.append(col)
    
    if null_cols:
        msg = f"Required columns contain null values: {null_cols}"
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        return False

    # 3. Check if empty
    if df.empty:
        msg = "Dataframe is empty."
        log.error(msg)
        _write_log_file(passed=False, details=msg)
        return False

    _write_log_file(passed=True)
    log.info("Data validation successful.")
    return True

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate VAERS data against schema.")
    parser.add_argument("--input", type=str, required=True, help="Path to data file.")
    parser.add_argument("--schema", type=str, default="specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml", help="Path to schema.")
    
    args = parser.parse_args()

    try:
        schema = load_schema(args.schema)
        df = _load_data(args.input)
        if not validate_data(df, schema):
            sys.exit(1)
    except Exception as e:
        log.error("Validation process failed: %s", e)
        _write_log_file(passed=False, details=str(e))
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
