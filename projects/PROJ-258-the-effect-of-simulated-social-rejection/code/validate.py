"""
Validation script for raw dataset parquet files.

This script scans the raw data directory for parquet files, validates each
file against the required schema, and writes a JSON validation report for
each dataset under ``data/interim``.

Required checks per dataset:
  * Presence of required columns:
      - participant_id
      - condition
      - reaction_time
      - mood_rating
  * The ``condition`` column must contain at least the two values
    ``rejection`` and ``control`` (case‑insensitive).
  * Basic value‑range checks:
      - ``reaction_time`` must be a non‑negative number.
      - ``mood_rating`` must be numeric and lie within the inclusive range
        [0, 10] (a generous bound covering typical Likert scales).

If any check fails the script logs the problem, writes a report with
``\"status\": \"fail\"``, and exits with status code 1.  Successful
validation yields ``\"status\": \"pass\"`` in the JSON report and the
script exits with status code 0.

The script is invoked from the quick‑start pipeline (or directly) as::

    python code/validate.py --raw data/raw/ds000208.parquet --schema contracts/dataset.schema.yaml --output data/interim/ingest_validation_report.json

"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import pyarrow.parquet as pq

from config import get_path

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "participant_id": ["participant_id", "participant", "id"],
    "condition": ["condition"],
    "reaction_time": ["reaction_time", "reaction time", "rt"],
    "mood_rating": ["mood_rating", "mood", "rating"],
}

def _detect_column(df: pd.DataFrame, candidates: List[str]) -> str:
    """
    Return the first column name in *df* that matches any entry in
    *candidates* (case‑insensitive). Raises ``ValueError`` if none match.
    """
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        cand_l = cand.lower()
        if cand_l in lower_map:
            return lower_map[cand_l]
    raise ValueError(
        f"Required column not found. Expected one of {candidates}. "
        f"Available columns: {list(df.columns)}"
    )

def _validate_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Verify that all required logical columns are present (allowing for
    common naming variations). Returns a mapping from logical name to the
    actual column name used in the DataFrame.
    """
    mapping = {}
    for logical, alternatives in REQUIRED_COLUMNS.items():
        try:
            actual = _detect_column(df, alternatives)
            mapping[logical] = actual
        except ValueError as exc:
            raise ValueError(str(exc))
    return mapping

def _validate_condition_values(series: pd.Series) -> None:
    """
    Ensure that the ``condition`` series contains at least the two
    required levels: ``rejection`` and ``control`` (case‑insensitive).
    """
    unique_vals = {str(v).lower() for v in series.dropna().unique()}
    missing = []
    for required in ("rejection", "control"):
        if required not in unique_vals:
            missing.append(required)
    if missing:
        raise ValueError(
            f"Condition column missing required values: {missing}. "
            f"Found: {sorted(unique_vals)}"
        )

def _validate_value_ranges(df: pd.DataFrame, mapping: Dict[str, str]) -> None:
    """
    Perform simple numeric range checks:

    * reaction_time >= 0
    * 0 <= mood_rating <= 10
    """
    rt_col = mapping["reaction_time"]
    mood_col = mapping["mood_rating"]

    # Reaction time non‑negative
    if (df[rt_col] < 0).any():
        raise ValueError("Negative values detected in reaction_time column.")

    # Mood rating numeric and within [0, 10]
    if not pd.api.types.is_numeric_dtype(df[mood_col]):
        raise ValueError("mood_rating column is not numeric.")
    if (df[mood_col] < 0).any() or (df[mood_col] > 10).any():
        raise ValueError(
            "mood_rating values fall outside the expected range [0, 10]."
        )

def validate_dataset(parquet_path: Path) -> Dict[str, Any]:
    """
    Validate a single parquet file and return a dictionary suitable for
    JSON serialisation.
    """
    logger.info(f"Validating dataset: {parquet_path}")
    try:
        # Try reading with pyarrow first with coerce_int96_timestamp_unit
        try:
            table = pq.read_table(
                parquet_path,
                coerce_int96_timestamp_unit='ns'
            )
            df = table.to_pandas()
        except Exception as pa_exc:
            logger.warning(f"PyArrow read failed, trying pandas: {pa_exc}")
            df = pd.read_parquet(parquet_path, engine='pyarrow')
    except Exception as exc:
        raise RuntimeError(f"Failed to read parquet file: {exc}")

    # 1. Required columns
    column_map = _validate_columns(df)

    # 2. Condition values
    _validate_condition_values(df[column_map["condition"]])

    # 3. Value ranges
    _validate_value_ranges(df, column_map)

    return {
        "status": "pass",
        "dataset": parquet_path.name,
        "columns_present": list(column_map.values()),
    }

def main() -> None:
    """
    Validate a single parquet file specified via --raw argument.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate raw dataset parquet files."
    )
    parser.add_argument(
        "--raw",
        required=True,
        help="Path to the raw parquet file to validate."
    )
    parser.add_argument(
        "--schema",
        help="Path to schema file (optional, for documentation)."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path where validation report JSON should be written."
    )
    
    args = parser.parse_args()
    
    parquet_path = Path(args.raw)
    output_path = Path(args.output)
    
    if not parquet_path.exists():
        logger.error(f"Parquet file not found: {parquet_path}")
        sys.exit(1)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        report = validate_dataset(parquet_path)
    except Exception as exc:
        logger.error(f"Validation failed for {parquet_path.name}: {exc}")
        report = {
            "status": "fail",
            "error": str(exc),
            "dataset": parquet_path.name,
        }

    # Write the report
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)

    logger.info(f"Validation report written to {output_path}")
    
    if report.get("status") == "fail":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
