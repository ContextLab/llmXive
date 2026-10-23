"""
Ingestion script for the Glass Forming Region prediction pipeline.

This script performs the following steps:
1. Downloads the experimental Critical Cooling Rate (CCR) dataset from a
   verified URL (configurable via the CCR_DATA_URL environment variable).
2. Streams elemental thermodynamic properties from the OQMD dataset
   (`matsci/oqmd`) using the Hugging Face `datasets` library.
3. Parses alloy compositions, validates that they are ternary, and filters
   out rows with missing or non‑numeric `critical_cooling_rate` or undefined
   `glass_forming_label`.
4. Logs every exclusion to `data/logs/exclusion_log.txt` and updates a
   JSON counter file `data/logs/label_filtering_status.json`.
5. Guards against an empty (or too small) dataset (< 500 rows) and writes
   a detailed traceback to `data/logs/empty_dataset_error.log` if the guard
   triggers.
6. Writes the cleaned, feature‑ready table to
   `data/processed/processed_alloys.csv`.
7. Records the SHA‑256 checksum of the final CSV in
   `data/logs/ingestion_hash.txt` (format: `<hash> processed_alloys.csv`).

All log files are created under `data/logs/`.  The script aborts on any
uncaught exception, ensuring the pipeline fails loudly rather than silently
falling back to synthetic data.
"""

import os
import sys
import json
import hashlib
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import pandas as pd
import requests
from datasets import load_dataset

# Local utilities (provided elsewhere in the repo)
from utils import get_logger, ensure_dir

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

# URL of the experimental CCR CSV.  It can be overridden at runtime by
# setting the environment variable `CCR_DATA_URL`.  The default points to a
# public GitHub raw file that is known to contain the required columns.
DEFAULT_CCR_URL = (
    "https://raw.githubusercontent.com/Materials-Data-Science-and-Informatics/"
    "Glass-Forming-Ability/master/data/experimental_ccr_dataset.csv"
)
CCR_DATA_URL = os.getenv("CCR_DATA_URL", DEFAULT_CCR_URL)

# OQMD elemental property dataset (streaming to keep memory usage low)
OQMD_DATASET_NAME = "matsci/oqmd"

# Directories (all created under the project root)
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# Output file names
RAW_CCR_PATH = os.path.join(RAW_DIR, "experimental_ccr_dataset.csv")
FINAL_CSV_PATH = os.path.join(PROCESSED_DIR, "processed_alloys.csv")
DOWNLOAD_LOG = os.path.join(LOGS_DIR, "download.log")
FETCH_ERROR_LOG = os.path.join(LOGS_DIR, "fetch_error.log")
EXCLUSION_LOG = os.path.join(LOGS_DIR, "exclusion_log.txt")
EMPTY_DATASET_ERROR_LOG = os.path.join(LOGS_DIR, "empty_dataset_error.log")
LABEL_FILTER_STATUS_JSON = os.path.join(LOGS_DIR, "label_filtering_status.json")
INGESTION_HASH_TXT = os.path.join(LOGS_DIR, "ingestion_hash.txt")

# Operational constants
MIN_VALID_ROWS = 500
RANDOM_STATE = 42
CHUNK_SIZE = 5000  # Used when streaming the OQMD dataset (not critical here)

# -------------------------------------------------------------------------
# Logger setup
# -------------------------------------------------------------------------

logger = get_logger(__name__)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def download_ccr_dataset(url: str, dest_path: str) -> None:
    """
    Download the CCR CSV from ``url`` and write it to ``dest_path``.
    Logs success to ``download.log``; on failure writes a concise entry
    to ``fetch_error.log`` and re‑raises the exception.
    """
    ensure_dir(LOGS_DIR)
    ensure_dir(RAW_DIR)

    logger.info(f"Attempting to download CCR dataset from {url}")

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Will raise for HTTP errors

        # Write to disk while streaming
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Log success
        with open(DOWNLOAD_LOG, "a") as log_f:
            log_f.write(
                f"{datetime.now().isoformat()} - SUCCESS - Downloaded CCR dataset to {dest_path}\n"
            )
        logger.info(f"CCR dataset downloaded successfully to {dest_path}")

    except Exception as exc:
        # Log the error and re‑raise so the caller can handle it uniformly
        error_msg = f"{datetime.now().isoformat()} - ERROR - {type(exc).__name__}: {exc}"
        with open(FETCH_ERROR_LOG, "w") as err_f:
            err_f.write(error_msg + "\n")
        logger.error(f"Failed to download CCR dataset: {exc}")
        raise

def stream_oqmd_properties():
    """
    Stream elemental properties from the OQMD dataset.

    Returns an iterator of dictionaries, each representing an element with
    at least the keys required by the feature‑engineering step
    (`atomic_radius`, `electronegativity`, etc.).
    """
    logger.info(f"Loading OQMD dataset '{OQMD_DATASET_NAME}' (streaming)")
    try:
        dataset = load_dataset(OQMD_DATASET_NAME, streaming=True)
        # The dataset usually has a single split; we take the first one.
        split_name = list(dataset.keys())[0]
        return dataset[split_name]
    except Exception as exc:
        # Propagate the exception – the pipeline must fail loudly if OQMD
        # cannot be accessed.
        logger.error(f"Failed to load OQMD dataset: {exc}")
        raise

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse an alloy composition string into a mapping ``element -> fraction``.

    Expected format examples: ``Fe40Ni40B20`` or ``Cu50Zr40Al10``.
    """
    if not isinstance(composition_str, str):
        return {}

    pattern = r"([A-Z][a-z]?)(\d*\.?\d*)"
    matches = re.findall(pattern, composition_str)

    result: Dict[str, float] = {}
    for element, amount_str in matches:
        if not amount_str:
            amount_str = "1"
        try:
            amount = float(amount_str)
            result[element] = amount
        except ValueError:
            continue
    return result

def validate_ternary_elements(elements: List[str]) -> bool:
    """
    Verify that exactly three distinct chemical symbols are present and
    that each symbol corresponds to a known element (using ``mendeleev``).
    """
    if len(elements) != 3:
        return False
    from mendeleev import element as mendeleev_element
    for el in elements:
        try:
            mendeleev_element(el)
        except Exception:
            return False
    return True

def write_exclusion_log(reasons: List[str]) -> None:
    """Write each exclusion reason to ``exclusion_log.txt``."""
    ensure_dir(LOGS_DIR)
    with open(EXCLUSION_LOG, "w") as f:
        for line in reasons:
            f.write(line + "\n")
    logger.info(f"Wrote {len(reasons)} exclusion reasons to {EXCLUSION_LOG}")

def update_label_filter_status(total: int, excluded: int) -> None:
    """
    Write a JSON file summarising how many rows were excluded during the
    label‑filtering step.
    """
    status = {
        "total_rows": total,
        "excluded": excluded,
        "included": total - excluded,
    }
    with open(LABEL_FILTER_STATUS_JSON, "w") as f:
        json.dump(status, f, indent=2)
    logger.info(f"Label filtering status written to {LABEL_FILTER_STATUS_JSON}")

def compute_sha256(file_path: str) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def write_hash_file(hash_hex: str, target_filename: str) -> None:
    """
    Write the hash line ``<hex> <filename>`` to ``ingestion_hash.txt``.
    """
    ensure_dir(LOGS_DIR)
    with open(INGESTION_HASH_TXT, "w") as f:
        f.write(f"{hash_hex} {target_filename}\n")
    logger.info(f"SHA‑256 hash written to {INGESTION_HASH_TXT}")

# -------------------------------------------------------------------------
# Core ingestion workflow
# -------------------------------------------------------------------------

def run_ingestion() -> None:
    """
    Main entry point for the ingestion pipeline.
    """
    logger.info("=== Starting ingestion pipeline ===")
    ensure_dir(LOGS_DIR)
    ensure_dir(PROCESSED_DIR)

    # -----------------------------------------------------------------
    # Step 1 – Download the experimental CCR CSV
    # -----------------------------------------------------------------
    try:
        download_ccr_dataset(CCR_DATA_URL, RAW_CCR_PATH)
    except Exception:
        # The download function already logged the error and wrote
        # ``fetch_error.log``.  We abort because the downstream steps depend
        # on the raw data.
        logger.critical("Aborting ingestion due to download failure.")
        sys.exit(1)

    # -----------------------------------------------------------------
    # Step 2 – Load the raw CCR data into a DataFrame
    # -----------------------------------------------------------------
    try:
        raw_df = pd.read_csv(RAW_CCR_PATH)
    except Exception as exc:
        logger.error(f"Failed to read downloaded CCR CSV: {exc}")
        # Record the failure in the same fetch‑error log for consistency
        with open(FETCH_ERROR_LOG, "a") as err_f:
            err_f.write(
                f"{datetime.now().isoformat()} - ERROR - Unable to parse CSV: {exc}\n"
            )
        sys.exit(1)

    # -----------------------------------------------------------------
    # Step 3 – Stream OQMD elemental properties (ensures dataset is
    #          reachable early in the pipeline)
    # -----------------------------------------------------------------
    try:
        _ = stream_oqmd_properties()  # iterator not used here, just for validation
    except Exception:
        logger.critical("Aborting ingestion because OQMD could not be loaded.")
        sys.exit(1)

    # -----------------------------------------------------------------
    # Step 4 – Filter and clean the CCR data
    # -----------------------------------------------------------------
    valid_rows: List[Dict] = []
    exclusion_reasons: List[str] = []

    for idx, row in raw_df.iterrows():
        # -------------------------------------------------------------
        # 4.1 – Critical cooling rate must be present and numeric
        # -------------------------------------------------------------
        ccr = row.get("critical_cooling_rate")
        if pd.isna(ccr):
            exclusion_reasons.append(
                f"Missing critical_cooling_rate: {row.get('composition', 'N/A')}"
            )
            continue
        try:
            _ = float(ccr)
        except (ValueError, TypeError):
            exclusion_reasons.append(
                f"Non‑numeric critical_cooling_rate: {row.get('composition', 'N/A')}"
            )
            continue

        # -------------------------------------------------------------
        # 4.2 – Composition string must be parseable and ternary
        # -------------------------------------------------------------
        comp_str = row.get("composition", "")
        if not isinstance(comp_str, str) or not comp_str.strip():
            exclusion_reasons.append(
                f"Invalid or missing composition: index {idx}"
            )
            continue

        comp_dict = parse_composition(comp_str)
        elements = list(comp_dict.keys())
        if not validate_ternary_elements(elements):
            exclusion_reasons.append(
                f"Not a valid ternary composition: {comp_str}"
            )
            continue

        # -------------------------------------------------------------
        # 4.3 – Optional glass_forming_label filtering
        # -------------------------------------------------------------
        if "glass_forming_label" in row:
            label = row["glass_forming_label"]
            if pd.isna(label):
                exclusion_reasons.append(
                    f"Missing glass_forming_label: {comp_str}"
                )
                continue
            # Keep only a predefined whitelist if needed
            valid_labels = {"amorphous", "crystalline", "glassy"}
            if label not in valid_labels:
                exclusion_reasons.append(
                    f"Invalid glass_forming_label ('{label}') for {comp_str}"
                )
                continue

        # -------------------------------------------------------------
        # 4.4 – Row passes all checks – add source label and keep it
        # -------------------------------------------------------------
        row_copy = row.to_dict()
        row_copy["source_label"] = CCR_DATA_URL  # provenance
        valid_rows.append(row_copy)

    # -----------------------------------------------------------------
    # Step 5 – Log exclusions and write status JSON
    # -----------------------------------------------------------------
    if exclusion_reasons:
        write_exclusion_log(exclusion_reasons)

    update_label_filter_status(
        total=len(raw_df), excluded=len(exclusion_reasons)
    )

    # -----------------------------------------------------------------
    # Step 6 – Guard against an empty (or too small) dataset
    # -----------------------------------------------------------------
    if len(valid_rows) < MIN_VALID_ROWS:
        error_msg = (
            "Dataset is empty after filtering. Check composition parsing logic "
            "and data source validity."
        )
        logger.error(error_msg)
        with open(EMPTY_DATASET_ERROR_LOG, "w") as f:
            f.write(
                f"{datetime.now().isoformat()} - ERROR: {error_msg}\n"
                + traceback.format_exc()
            )
        raise ValueError(error_msg)

    # -----------------------------------------------------------------
    # Step 7 – Write the cleaned CSV
    # -----------------------------------------------------------------
    clean_df = pd.DataFrame(valid_rows)
    clean_df.to_csv(FINAL_CSV_PATH, index=False)
    logger.info(
        f"Wrote {len(clean_df)} cleaned rows to {FINAL_CSV_PATH}"
    )

    # -----------------------------------------------------------------
    # Step 8 – Compute and record SHA‑256 hash
    # -----------------------------------------------------------------
    hash_hex = compute_sha256(FINAL_CSV_PATH)
    write_hash_file(hash_hex, os.path.basename(FINAL_CSV_PATH))

    logger.info("=== Ingestion pipeline completed successfully ===")

# -------------------------------------------------------------------------
# Script entry point
# -------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_ingestion()
    except Exception as e:
        # Any unexpected exception is logged and results in a non‑zero exit
        logger.exception(f"Unhandled exception in ingestion: {e}")
        sys.exit(1)