"""
Raw VAERS dataset validation script (T003).

Provides a command‑line interface:
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

import pandas as pd
import yaml
from llmxive_toolkit import paths, get_logger

# Re‑use the core validation helpers from src.data.validate
from src.data.validate import (
    load_schema,
    _load_data,
    validate_data,
    _write_log_file as _write_generic_log,
)

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

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate raw VAERS parquet file against a JSON‑Schema."
    )
    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Path to the JSON‑Schema YAML file.",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the raw VAERS parquet (or CSV) file to validate.",
    )
    args = parser.parse_args()

    try:
        schema = load_schema(args.schema)
        df = _load_data(args.input)
        if not validate_data(df, schema):
            # validate_data already wrote generic logs; we write raw‑specific fail log
            _write_log_file(passed=False, details="Schema validation failed.")
            sys.exit(1)
    except Exception as exc:
        log.error("Validation process failed: %s", exc)
        _write_log_file(passed=False, details=str(exc))
        sys.exit(1)

    # Success
    _write_log_file(passed=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
