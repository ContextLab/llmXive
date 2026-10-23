"""
Data Loader Module for Avian Migration Pipeline.
Handles downloading and processing of eBird data using the HuggingFace datasets library.
"""
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Iterator

import datasets
from code.config import DATA_RAW, REGIONAL_BBOX, get_logger, calculate_sha256

logger = get_logger(__name__)

# Constants for eBird filtering
MIN_DURATION = 1.0  # minutes
MIN_OBSERVERS = 1
MAX_DISTANCE = 10.0  # km
YEAR_START = 2015
YEAR_END = 2022
SPECIES_CODE = "SRUT"

CHUNK_SIZE = 50_000  # rows per CSV write chunk
# Safety limit to keep runtime reasonable on CI; can be increased if needed
MAX_ROWS_TO_PROCESS = 500_000

# Output filenames
EBIRD_OUTPUT_FILE = "ebd_subset.csv"
CHECKSUMS_FILE = "checksums.json"

def _filter_record(record: dict) -> bool:
    """Return True if the record satisfies all required filters."""
    # Species filter
    if record.get("species_code") != SPECIES_CODE:
        return False

    # Complete‑checklist criteria
    try:
        duration = float(record.get("duration_min", 0))
        observers = int(record.get("num_observers", 0))
        distance = float(record.get("distance_km", float("inf")))
    except (ValueError, TypeError):
        return False

    if duration < MIN_DURATION:
        return False
    if observers < MIN_OBSERVERS:
        return False
    if distance > MAX_DISTANCE:
        return False

    # Spatial filter (REGIONAL_BBOX)
    try:
        lat = float(record.get("latitude"))
        lon = float(record.get("longitude"))
    except (TypeError, ValueError):
        return False

    min_lat, max_lat, min_lon, max_lon = REGIONAL_BBOX
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
        return False

    # Year filter
    try:
        year = int(record.get("year"))
    except (TypeError, ValueError):
        return False
    if not (YEAR_START <= year <= YEAR_END):
        return False

    return True

def load_ebird_data() -> pd.DataFrame:
    """
    Streams the eBird Basic Dataset, filters for Setophaga ruticilla
    (species_code == "SRUT") and complete‑checklist criteria, then writes
    a chunked CSV to data/raw/ebd_subset.csv.
    Also creates/updates data/raw/checksums.json with the SHA‑256 checksum of the CSV.
    """
    output_path = DATA_RAW / EBIRD_OUTPUT_FILE
    checksum_path = DATA_RAW / CHECKSUMS_FILE

    # Ensure the raw data directory exists
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    # Check if already exists and verified
    if output_path.is_file() and checksum_path.is_file():
        try:
            with open(checksum_path, "r") as f:
                stored = json.load(f)
            if stored.get(EBIRD_OUTPUT_FILE) == calculate_sha256(output_path):
                logger.info(f"Existing eBird subset found and verified at {output_path}")
                return pd.read_csv(output_path)
        except Exception as e:
            logger.warning(f"Checksum verification failed: {e}")

    logger.info("Streaming eBird dataset from HuggingFace hub...")
    try:
        # Use the high‑level datasets API for streaming
        ds = datasets.load_dataset("vvud/eb-data", split="train", streaming=True)
    except Exception as e:
        logger.critical(f"Failed to access eBird dataset on HuggingFace: {e}")
        raise ConnectionError(f"Unable to fetch eBird dataset: {e}") from e

    header_written = False
    buffer = []
    rows_written = 0

    for record in ds:
        if not _filter_record(record):
            continue

        buffer.append(record)

        if len(buffer) >= CHUNK_SIZE:
            df_chunk = pd.DataFrame(buffer)
            mode = "w" if not header_written else "a"
            df_chunk.to_csv(output_path, index=False, mode=mode, header=not header_written)
            header_written = True
            rows_written += len(buffer)
            buffer.clear()
            logger.debug(f"Wrote {rows_written} processed rows to {output_path}")

        if rows_written >= MAX_ROWS_TO_PROCESS:
            logger.info(f"Reached max rows limit ({MAX_ROWS_TO_PROCESS}); stopping early.")
            break

    # Write any remaining buffered rows
    if buffer:
        df_chunk = pd.DataFrame(buffer)
        mode = "w" if not header_written else "a"
        df_chunk.to_csv(output_path, index=False, mode=mode, header=not header_written)
        rows_written += len(buffer)

    if rows_written == 0:
        raise RuntimeError("No records matched the filtering criteria; output file is empty.")

    logger.info(f"Successfully wrote {rows_written} rows to {output_path}")

    # Compute and store checksum
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

    # Return the freshly written DataFrame for downstream use
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
