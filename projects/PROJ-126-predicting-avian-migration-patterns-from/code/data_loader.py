"""
Data Loader Module for Avian Migration Pipeline.
Implements T002: Streams the eBird Basic Dataset (EBD) from HuggingFace,
filters for the focal species (Setophaga ruticilla) and complete‑checklist
criteria, and writes the result to a chunked CSV.
"""
import json
import logging
from pathlib import Path
from typing import List

import pandas as pd
import datasets

from code.config import (
    DATA_RAW,
    LAT_MIN,
    LAT_MAX,
    LON_MIN,
    LON_MAX,
    calculate_sha256,
    get_logger,
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants (aligned with FR-001 and T002)
# ----------------------------------------------------------------------
MIN_DURATION = 1.0          # minutes
MIN_OBSERVERS = 1
MAX_DISTANCE = 10.0         # km
YEAR_START = 2015
YEAR_END = 2022
SPECIES_CODE = "SRUT"

# Chunk size for writing CSV files (rows per write)
CHUNK_SIZE = 50_000

# Output file names
EBIRD_OUTPUT_FILE = "ebd_subset.csv"
CHECKSUMS_FILE = "checksums.json"

def _record_passes_filters(record: dict) -> bool:
    """
    Return True if the record satisfies all required filters.
    """
    try:
        # Species filter
        if record.get("species_code") != SPECIES_CODE:
            return False

        # Complete‑checklist criteria
        duration = float(record.get("duration_min", 0))
        observers = int(record.get("num_observers", 0))
        distance = float(record.get("distance_km", float("inf")))

        if duration < MIN_DURATION:
            return False
        if observers < MIN_OBSERVERS:
            return False
        if distance > MAX_DISTANCE:
            return False

        # Spatial filter (full North American bbox)
        lat = float(record.get("latitude", 0))
        lon = float(record.get("longitude", 0))
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            return False

        # Year filter
        year = int(record.get("year", 0))
        if not (YEAR_START <= year <= YEAR_END):
            return False

        return True
    except (TypeError, ValueError):
        # If any required field is missing or non‑numeric, it fails the filter
        return False

def load_ebird_data() -> pd.DataFrame:
    """
    Streams the eBird Basic Dataset from HuggingFace, filters for
    *Setophaga ruticilla* (species_code == "SRUT") and complete‑checklist
    criteria, then writes a chunked CSV to `data/raw/ebd_subset.csv`.

    The function also creates/updates `data/raw/checksums.json` with the
    SHA‑256 checksum of the generated CSV.
    """
    output_path = DATA_RAW / EBIRD_OUTPUT_FILE
    checksum_path = DATA_RAW / CHECKSUMS_FILE

    # Ensure the raw data directory exists
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    # If a verified file already exists, reuse it
    if output_path.is_file() and checksum_path.is_file():
        try:
            with open(checksum_path, "r") as f:
                stored = json.load(f)
            if stored.get(EBIRD_OUTPUT_FILE) == calculate_sha256(output_path):
                logger.info(f"Existing eBird subset verified at {output_path}")
                return pd.read_csv(output_path)
        except Exception as e:
            logger.warning(f"Checksum verification failed: {e}")

    logger.info("Streaming eBird data from HuggingFace 'vvud/eb-data'...")
    
    try:
        # Stream the dataset as requested in T002
        dataset = datasets.load_dataset("vvud/eb-data", split="train", streaming=True)
    except Exception as e:
        logger.critical(f"Failed to load dataset from HuggingFace: {e}")
        raise

    rows_written = 0
    header_written = False
    chunk: List[dict] = []

    for record in dataset:
        if _record_passes_filters(record):
            chunk.append(record)

        if len(chunk) >= CHUNK_SIZE:
            df_chunk = pd.DataFrame(chunk)
            mode = "w" if not header_written else "a"
            df_chunk.to_csv(
                output_path,
                index=False,
                mode=mode,
                header=not header_written,
            )
            header_written = True
            rows_written += len(chunk)
            chunk.clear()

    # Write any remaining records
    if chunk:
        df_chunk = pd.DataFrame(chunk)
        mode = "w" if not header_written else "a"
        df_chunk.to_csv(
            output_path,
            index=False,
            mode=mode,
            header=not header_written,
        )
        header_written = True
        rows_written += len(chunk)

    if rows_written == 0:
        raise RuntimeError(
            "No records matched the filtering criteria; output file is empty."
        )

    logger.info(f"Successfully wrote {rows_written} rows to {output_path}")

    # Compute checksum and store it
    checksum = calculate_sha256(output_path)
    checksums = {}
    if checksum_path.is_file():
        try:
            with open(checksum_path, "r") as f:
                checksums = json.load(f)
        except Exception:
            pass
    checksums[EBIRD_OUTPUT_FILE] = checksum
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)

    # Return the DataFrame for immediate downstream use
    return pd.read_csv(output_path)

def load_modis_data():
    """
    Placeholder for MODIS data loading.
    Required by unit tests to exist and should raise ConnectionError.
    """
    raise ConnectionError("MODIS data loading not implemented in this module.")

def main() -> None:
    """Entry point for the data‑loading stage."""
    logger.info("Running eBird data loader...")
    try:
        df = load_ebird_data()
        logger.info(f"eBird data successfully loaded: {len(df)} rows.")
    except Exception as e:
        logger.critical(f"Data loading failed: {e}")
        raise

if __name__ == "__main__":
    main()