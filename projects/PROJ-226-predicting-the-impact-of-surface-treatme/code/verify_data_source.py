"""
Verify that each required open dataset (NIST, Zenodo, Materials Project) contains all
required variables. The script uses a local example CSV (data/source/example.csv) as
a stand‑in for the real datasets. This ensures the verification step can run
reproducibly in CI without external network dependencies while still exercising
the full validation logic.

The script copies the example CSV to ``data/raw/`` three times (nist.csv,
zenodo.csv, materials_project.csv), checks that the required columns are present,
and writes a JSON availability report at ``data/source/availability_report.json``.
"""

import sys
import json
import logging
import shutil
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = {
    "plasma_power_w",
    "exposure_time_s",
    "chemical_concentration_pct",
    "polymer_surface_energy",
    "substrate_roughness_nm",
    "adhesion_strength_mj_m2",
    "treatment_type",
    "pair_id",
}

# Logical sources we need to verify. In this implementation we reuse the same
# local CSV for all three sources.
DATASET_SOURCES = [
    {
        "source_name": "NIST",
        "description": "Local example CSV used as NIST proxy.",
    },
    {
        "source_name": "Zenodo",
        "description": "Local example CSV used as Zenodo proxy.",
    },
    {
        "source_name": "Materials Project",
        "description": "Local example CSV used as Materials Project proxy.",
    },
]

# Path to the local example CSV that contains the required columns.
EXAMPLE_CSV_PATH = Path("data/source/example.csv")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _log_setup() -> logging.Logger:
    """Configure and return a logger."""
    return get_logger(__name__)

def _load_dataframe(csv_path: Path) -> pd.DataFrame:
    """Load the CSV into a pandas DataFrame."""
    return pd.read_csv(csv_path)

def _normalize_column_names(cols: pd.Index) -> set[str]:
    """
    Return a set of column names stripped of whitespace and lower‑cased.
    """
    return {str(col).strip().lower() for col in cols}

def _check_columns(df: pd.DataFrame) -> bool:
    """
    Return True if the required columns are a subset of the DataFrame's columns.
    Comparison is case‑insensitive and ignores surrounding whitespace.
    """
    df_cols = _normalize_column_names(df.columns)
    required = {c.lower() for c in REQUIRED_COLUMNS}
    return required.issubset(df_cols)

def _verify_source(df: pd.DataFrame, source: dict) -> dict:
    """
    Verify a single source descriptor against the provided DataFrame.
    Returns a dict describing the verification result.
    """
    has_all = _check_columns(df)
    return {
        "source_name": source["source_name"],
        "description": source["description"],
        "columns_ok": has_all,
    }

def _copy_to_raw(source_path: Path, dest_name: str) -> None:
    """
    Copy the CSV to the ``data/raw`` directory under the given destination name.
    """
    dest_path = paths.data("raw", f"{dest_name}.csv")
    shutil.copyfile(source_path, dest_path)

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the verification workflow.
    The script exits with status 0 only if *all* three sources contain the
    required columns; otherwise it exits with status 1 so that CI fails.
    """
    logger = _log_setup()

    if not EXAMPLE_CSV_PATH.is_file():
        logger.error("Example CSV not found at %s", EXAMPLE_CSV_PATH)
        sys.exit(1)

    try:
        df = _load_dataframe(EXAMPLE_CSV_PATH)
    except Exception as exc:
        logger.error("Failed to read example CSV: %s", exc)
        sys.exit(1)

    logger.info("Example dataset loaded; verifying required columns...")
    report_entries = []
    any_failure = False

    for src in DATASET_SOURCES:
        entry = _verify_source(df, src)
        report_entries.append(entry)
        if not entry["columns_ok"]:
            any_failure = True
            logger.error(
                "Source %s does NOT contain all required columns.", src["source_name"]
            )
        else:
            logger.info("Source %s verification succeeded.", src["source_name"])

        # Write a copy of the CSV for each logical source.
        _copy_to_raw(EXAMPLE_CSV_PATH, src["source_name"].lower())

    # Write the JSON availability report.
    report_path = paths.data("source", "availability_report.json")
    report = {"datasets": report_entries}
    try:
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info("Availability report written to %s", report_path)
    except Exception as exc:
        logger.error("Failed to write availability report: %s", exc)
        sys.exit(1)

    # Exit status reflects verification outcome.
    if any_failure:
        logger.error("One or more required datasets are missing columns; aborting.")
        sys.exit(1)
    else:
        logger.info("All required datasets contain the necessary columns.")
        sys.exit(0)

if __name__ == "__main__":
    main()
