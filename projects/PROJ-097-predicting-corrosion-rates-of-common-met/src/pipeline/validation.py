"""Validation script for ingestion and cleaning pipeline (T002_val).

This script runs the ingestion → cleaning pipeline three times on a held‑out
validation CSV (``data/validation/validation_subset.csv``).  For each run it
checks that:

1. No runtime error occurs.
2. All required columns are present in the cleaned output.
3. Required columns contain zero null values.

The empirical pass‑rate (number of successful runs / 3) is written to
``data/results/ingestion_validation_metrics.json`` under the key
``pass_rate``.  A pass‑rate of at least 0.95 satisfies SC‑007.

The script deliberately avoids external network calls; it re‑uses the
existing ``clean_dataset`` function from ``src.pipeline.clean`` which
already implements column validation, unit harmonisation, imputation,
standardisation and one‑hot encoding.  The validation CSV must therefore
conform to the same schema as the main dataset.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

from llmxive_toolkit import paths, get_logger

# Import the cleaning routine – this is the core of T002.
from src.pipeline.clean import clean_dataset

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "ph",
    "salinity",
    "temperature",
    "composition",
    "corrosion_rate",
    "source_id",
]

VALIDATION_CSV = paths.data("validation", "validation_subset.csv")
# The cleaned files are written to a temporary location; they are not
# needed after the script finishes, but we keep them to make debugging
# easier.
CLEANED_DIR = paths.data("processed", "validation_runs")
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = paths.results("ingestion_validation_metrics.json")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_one_pass(run_index: int) -> bool:
    """Run ingest → clean once and return whether the run succeeded.

    The function catches any exception raised by ``clean_dataset`` and
    records detailed log messages.  If the cleaned CSV is produced, the
    required‑column and null‑value checks are performed.
    """
    try:
        # In the original pipeline the ingestion step would download a raw
        # CSV.  For validation we simply treat the held‑out CSV as the raw
        # input.
        raw_path = VALIDATION_CSV
        cleaned_path = CLEANED_DIR / f"cleaned_dataset_val_{run_index}.csv"

        log.info("Validation run %s: cleaning %s → %s", run_index, raw_path, cleaned_path)
        clean_dataset(str(raw_path), str(cleaned_path))

    except Exception as exc:  # pragma: no cover – defensive
        log.error("Run %s failed during cleaning: %s", run_index, exc, exc_info=True)
        return False

    # ------------------------------------------------------------------
    # Verify required columns and nulls
    # ------------------------------------------------------------------
    try:
        import pandas as pd

        df = pd.read_csv(cleaned_path)
    except Exception as exc:  # pragma: no cover
        log.error("Run %s could not read cleaned CSV: %s", run_index, exc)
        return False

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        log.error("Run %s missing required columns: %s", run_index, missing)
        return False

    null_counts = {c: int(df[c].isna().sum()) for c in REQUIRED_COLUMNS}
    if any(v > 0 for v in null_counts.values()):
        log.error(
            "Run %s contains nulls in required columns: %s",
            run_index,
            {k: v for k, v in null_counts.items() if v > 0},
        )
        return False

    log.info("Run %s passed all validation checks.", run_index)
    return True

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """Execute three validation runs and write the pass‑rate JSON."""
    if not VALIDATION_CSV.is_file():
        log.error("Validation CSV not found at %s", VALIDATION_CSV)
        return 1

    successes = 0
    total_runs = 3
    for i in range(total_runs):
        if _run_one_pass(i):
            successes += 1

    pass_rate = successes / total_runs
    result = {"pass_rate": pass_rate}
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)

    log.info("Ingestion‑validation pass‑rate: %.3f (%d/%d)", pass_rate, successes, total_runs)
    # The verification criterion requires pass_rate >= 0.95.
    return 0 if pass_rate >= 0.95 else 1

if __name__ == "__main__":
    raise SystemExit(main())
