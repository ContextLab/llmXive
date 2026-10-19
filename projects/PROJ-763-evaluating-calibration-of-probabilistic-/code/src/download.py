"""
download.py
-------------
This script implements the **Data Availability Gate** for the SubseasonalRodeo
dataset. After the raw dataset has been downloaded and extracted (handled by
the earlier T001 task), this script scans the extracted parquet files and
verifies that at least one of the required probability fields
``probability_value`` or ``precip_prob`` is present.

If the required field is missing from **all** parquet files, the script logs
an error message ``Data Availability Gate Failed`` and exits with status
code 1, satisfying FR‑001 / SC‑007.

The script is deliberately lightweight: it does not perform any synthetic
fallback, does not modify data, and only relies on the standard library,
``pandas`` (already available in the environment), and the ``llmxive_toolkit``
utilities for path handling and logging.
"""

import sys
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

def _find_parquet_files(root: Path):
    """
    Recursively locate all ``*.parquet`` files under the given root directory.
    """
    parquet_files = list(root.rglob("*.parquet"))
    if not parquet_files:
        log.error(f"No parquet files found under {root}")
    return parquet_files

def _has_required_field(df_columns: set) -> bool:
    """
    Return ``True`` if the column set contains either ``probability_value``
    or ``precip_prob``.
    """
    required = {"probability_value", "precip_prob"}
    return bool(required.intersection(df_columns))

def data_availability_gate() -> None:
    """
    Perform the Data Availability Gate check.

    - Scans all parquet files in ``data/raw``.
    - If any file contains at least one of the required fields, the gate
      passes and the script exits with code 0.
    - Otherwise, logs an error and exits with code 1.
    """
    raw_dir = paths.data("raw")
    if not raw_dir.exists():
        log.error(f"Raw data directory does not exist: {raw_dir}")
        sys.exit(1)

    parquet_files = _find_parquet_files(raw_dir)
    if not parquet_files:
        log.error("Data Availability Gate Failed: no parquet files to inspect.")
        sys.exit(1)

    for parquet_path in parquet_files:
        try:
            # Load only the schema (column names) to avoid unnecessary I/O.
            # ``read_parquet`` with ``columns=[]`` would raise; instead we read
            # a small chunk if the file is large. Here we read the full file
            # because column metadata is needed; this is acceptable for the
            # typical SubseasonalRodeo parquet size.
            df = pd.read_parquet(parquet_path)
        except Exception as exc:
            log.error(f"Failed to read parquet file {parquet_path}: {exc}")
            sys.exit(1)

        cols = set(df.columns)
        if _has_required_field(cols):
            log.info(
                f"Data Availability Gate passed – required field found in "
                f"{parquet_path.name}"
            )
            # Successful gate; exit with 0.
            return

    # If we reach this point, none of the files contained the required fields.
    log.error("Data Availability Gate Failed")
    sys.exit(1)

if __name__ == "__main__":
    data_availability_gate()