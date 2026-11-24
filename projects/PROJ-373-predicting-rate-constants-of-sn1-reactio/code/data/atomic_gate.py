"""
code/data/atomic_gate.py
Consolidated gate script for SN1 data ingestion.

Performs the following steps:
1. Checks that required metadata columns (temperature, solvent, substrate_class)
   are present in the source datasets.
2. Downloads the verified HuggingFace datasets (streaming) and merges them.
3. Writes the merged dataset to `data/raw/sn1_raw_merged.parquet`.
4. Initializes an empty exclusion log at `data/processed/exclusion_raw.log`.
5. Writes pipeline status to `data/processed/.pipeline_status` (OK on success,
   ABORTED on any fatal failure).

If any required column is missing, the script writes 'ABORTED' to the status
file, logs a fatal error, and exits with code 1.
"""

import sys
import csv
import logging
from pathlib import Path

import pandas as pd

# External library for dataset download – must be present in the environment.
try:
    from datasets import load_dataset
except ImportError as exc:
    print("ERROR: The 'datasets' library is required. Install with 'pip install datasets'.")
    raise exc

# llmxive utilities – always available in the project environment.
from llmxive_toolkit import paths, get_logger

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
DATASET_NAMES = [
    "DTS-SN1-15-01-2024",
    "SN18-All-20240204"
]

REQUIRED_COLUMNS = ["temperature", "solvent", "substrate_class"]

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def write_status(status_path: Path, status: str) -> None:
    """Write the pipeline status string to the given path."""
    # If a directory exists at the status path, remove it first.
    if status_path.is_dir():
        # This situation should not happen, but we clean it up to avoid IsADirectoryError.
        for child in status_path.iterdir():
            child.unlink()
        status_path.rmdir()
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(status, encoding="utf-8")

def init_exclusion_log(log_path: Path) -> None:
    """Create an empty exclusion log with the required header."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["row_index", "reason", "original_smiles"])

def abort_pipeline(status_path: Path, log_path: Path, logger: logging.Logger, reason: str) -> None:
    """Handle a fatal error: log, write ABORTED status, create empty exclusion log, exit."""
    logger.error(f"FATAL: {reason}")
    write_status(status_path, "ABORTED")
    init_exclusion_log(log_path)
    sys.exit(1)

# -------------------------------------------------------------------------
# Main execution
# -------------------------------------------------------------------------
def main() -> None:
    logger = get_logger(__name__)

    # Define output locations using the llmxive path helpers.
    raw_parquet_path = paths.data("raw", "sn1_raw_merged.parquet")
    exclusion_log_path = paths.data("processed", "exclusion_raw.log")
    status_path = paths.data("processed", ".pipeline_status")

    # -----------------------------------------------------------------
    # Step 1 – Download and stream each dataset.
    # -----------------------------------------------------------------
    all_rows = []
    for ds_name in DATASET_NAMES:
        logger.info(f"Starting download (streaming) for dataset: {ds_name}")
        try:
            # Removed trust_remote_code as it is no longer supported.
            ds = load_dataset(
                ds_name,
                split="train",
                streaming=True
            )
        except Exception as e:
            logger.error(f"Failed to load dataset {ds_name}: {e}")
            abort_pipeline(status_path, exclusion_log_path, logger,
                           f"download_failure:{ds_name}")

        count = 0
        for row in ds:
            all_rows.append(row)
            count += 1
            if count % 10000 == 0:
                logger.info(f"Downloaded {count} rows from {ds_name}...")

        logger.info(f"Completed download of {count} rows from {ds_name}")

    if not all_rows:
        abort_pipeline(status_path, exclusion_log_path, logger,
                       "no_data_downloaded")

    # -----------------------------------------------------------------
    # Step 2 – Convert to DataFrame and validate required columns.
    # -----------------------------------------------------------------
    logger.info("Converting downloaded rows to pandas DataFrame")
    df = pd.DataFrame(all_rows)

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required metadata columns: {missing_cols}")
        abort_pipeline(status_path, exclusion_log_path, logger,
                       f"missing_metadata:{missing_cols}")

    # -----------------------------------------------------------------
    # Step 3 – Write merged Parquet file.
    # -----------------------------------------------------------------
    raw_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving merged dataset to Parquet: {raw_parquet_path}")
    try:
        df.to_parquet(raw_parquet_path, index=False)
    except Exception as e:
        logger.error(f"Failed to write Parquet file: {e}")
        abort_pipeline(status_path, exclusion_log_path, logger,
                       "parquet_write_failure")

    # -----------------------------------------------------------------
    # Step 4 – Initialise exclusion log (empty, with header).
    # -----------------------------------------------------------------
    init_exclusion_log(exclusion_log_path)

    # -----------------------------------------------------------------
    # Step 5 – Write successful pipeline status.
    # -----------------------------------------------------------------
    write_status(status_path, "OK")
    logger.info("Atomic gate completed successfully. Pipeline status set to OK.")

if __name__ == "__main__":
    main()