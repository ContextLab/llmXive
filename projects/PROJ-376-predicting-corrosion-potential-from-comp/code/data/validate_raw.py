"""
validate_raw.py
----------------
Schema‑validation step for the raw NIST ingest.

This script loads all CSV files found under ``data/raw/`` (produced by the
``download_nist`` stage), validates each record against the
``ingest.schema.yaml`` contract, enforces the presence of the required
fields, and checks the minimum‑record constraints required by the
specification (FR‑011, FR‑014, FR‑017).

On success a JSON summary is written to ``data/logs/schema_validation.json``
and the script exits with status 0.  If any validation rule fails a
``SchemaMismatchError`` is raised, causing a non‑zero exit status.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import yaml

from llmxive_toolkit import paths, get_logger
from code.utils.exceptions import SchemaMismatchError

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Required columns that must be present and non‑null in every record.
REQUIRED_COLUMNS = [
    "composition",               # JSON / string representation of elemental fractions
    "ph",                        # aqueous pH (numeric)
    "temperature_celsius",       # temperature in °C (numeric)
    "corrosion_potential_mV",    # target variable
]

# Column that identifies a specific alloy designation (used for the
# unique‑alloy count).  If it does not exist we treat the count as 0.
ALLOY_ID_COLUMN = "specific_alloy_designation"

# Minimum thresholds (from FR‑014, FR‑017)
MIN_RECORDS = 500
MIN_UNIQUE_ALLOYS = 10

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def find_csv_files(root: Path) -> List[Path]:
    """Return a list of all ``*.csv`` files under ``root`` (recursive)."""
    return list(root.rglob("*.csv"))

def load_raw_dataset(csv_paths: List[Path]) -> pd.DataFrame:
    """Load and concatenate all CSV files found under ``data/raw/``."""
    if not csv_paths:
        raise SchemaMismatchError("No CSV files found in the raw data directory.")
    dfs = []
    for p in csv_paths:
        log.info(f"Loading raw CSV: {p}")
        df = pd.read_csv(p)
        dfs.append(df)
    combined = pd.concat(dfs, ignore_index=True)
    log.info(f"Combined raw dataset shape: {combined.shape}")
    return combined

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON‑Schema (YAML) file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Very lightweight schema validation.

    The full JSON‑Schema validator is provided elsewhere (``utils.validate_schemas``);
    here we only check that the required top‑level keys exist and are of the
    expected type when the schema defines ``type`` for them.
    """
    errors: List[str] = []
    properties = schema.get("properties", {})
    for field, definition in properties.items():
        if field not in record:
            errors.append(f"Missing field '{field}'")
            continue
        # Basic type check (only a subset of JSON‑Schema types)
        expected_type = definition.get("type")
        if expected_type:
            value = record[field]
            if expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' expected number, got {type(value).__name__}")
            elif expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' expected string, got {type(value).__name__}")
    return errors

def perform_validation(df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate each record and collect violations.

    Returns a list of violation dictionaries:
    {
        "index": <row index>,
        "errors": [list of error strings]
    }
    """
    violations: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        record = row.to_dict()
        errors: List[str] = []

        # 1. Required columns must be present and non‑null
        for col in REQUIRED_COLUMNS:
            if col not in record:
                errors.append(f"Missing required column '{col}'")
            elif pd.isna(record[col]):
                errors.append(f"Null value in required column '{col}'")

        # 2. Run the lightweight schema check
        schema_errors = validate_against_schema(record, schema)
        errors.extend(schema_errors)

        if errors:
            violations.append({"index": int(idx), "errors": errors})
    return violations

def write_summary(
    total_records: int,
    unique_alloys: int,
    violations: List[Dict[str, Any]],
    summary_path: Path,
) -> None:
    """Write the JSON summary file required by the task."""
    summary = {
        "total_records": total_records,
        "unique_alloy_designations": unique_alloys,
        "violation_count": len(violations),
        "violations": violations,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Schema validation summary written to {summary_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the raw‑data schema validation.

    Expected locations:
    - Raw CSVs: ``data/raw/`` (any sub‑directory)
    - Ingest schema: ``specs/001-predicting-corrosion-potential-from-comp/contracts/ingest.schema.yaml``
    - Output summary: ``data/logs/schema_validation.json``
    """
    raw_root = paths.data("raw")
    csv_files = find_csv_files(raw_root)
    df = load_raw_dataset(csv_files)

    # Load the ingest schema
    schema_path = (
        paths.root
        / "specs"
        / "001-predict-corrosion-potential-from-comp"
        / "contracts"
        / "ingest.schema.yaml"
    )
    if not schema_path.is_file():
        raise SchemaMismatchError(f"Ingest schema not found at expected path: {schema_path}")

    schema = load_schema(schema_path)

    # Perform validation
    violations = perform_validation(df, schema)

    # Compute unique alloy count (if the column exists)
    if ALLOY_ID_COLUMN in df.columns:
        unique_alloys = int(df[ALLOY_ID_COLUMN].nunique())
    else:
        unique_alloys = 0
        log.warning(
            f"Column '{ALLOY_ID_COLUMN}' not found in raw data – unique alloy count set to 0."
        )

    # Write the summary JSON
    summary_path = paths.logs("schema_validation.json")
    write_summary(len(df), unique_alloys, violations, summary_path)

    # Enforce minimum‑record constraints
    if len(df) < MIN_RECORDS:
        raise SchemaMismatchError(
            f"Record count {len(df)} is below the required minimum of {MIN_RECORDS}."
        )
    if unique_alloys < MIN_UNIQUE_ALLOYS:
        raise SchemaMismatchError(
            f"Unique alloy designations {unique_alloys} is below the required minimum of {MIN_UNIQUE_ALLOYS}."
        )
    if violations:
        raise SchemaMismatchError(
            f"Schema validation found {len(violations)} record violations; see {summary_path} for details."
        )

    log.info("Raw schema validation completed successfully; all criteria satisfied.")

if __name__ == "__main__":
    main()
