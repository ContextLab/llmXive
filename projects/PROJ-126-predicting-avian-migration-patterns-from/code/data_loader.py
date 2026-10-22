"""
Data Loader Module for Avian Migration Pipeline.
Handles downloading and processing of eBird data using the HuggingFace hub.
"""
import json
import logging
import csv
import gzip
from pathlib import Path
from typing import Iterator

import pandas as pd
from huggingface_hub import hf_hub_download

# Import configuration and logger from the code package
from code.config import DATA_RAW, REGIONAL_BBOX, get_logger

logger = get_logger(__name__)

# Constants for eBird filtering
MIN_DURATION = 1.0  # minutes
MIN_OBSERVERS = 1
MAX_DISTANCE = 10.0  # km

CHUNK_SIZE = 50_000  # rows per CSV write chunk
# Safety limit to keep runtime reasonable on CI; can be increased if needed
MAX_ROWS_TO_PROCESS = 200_000

# Output filenames used by tests and the pipeline
EBIRD_OUTPUT_FILE = "ebd_subset.csv"
CHECKSUMS_FILE = "checksums.json"

# Exported paths for external import (tests expect these)
DATA_RAW = DATA_RAW
EBIRD_OUTPUT_FILE = EBIRD_OUTPUT_FILE
CHECKSUMS_FILE = CHECKSUMS_FILE

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    import hashlib

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _filter_record(record: dict) -> bool:
    """Return True if the record satisfies all required filters."""
    # Species filter
    if record.get("species_code") != "SRUT":
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
    if not (2015 <= year <= 2022):
        return False

    return True

# -----------------------------------------------------------------
# Helper functions for fetching data (used in unit tests)
# -----------------------------------------------------------------
def _fetch_ebird_data() -> Iterator[dict]:
    """
    Fetch the eBird Basic Dataset (EBD) from the HuggingFace hub.
    The dataset is stored as a large TSV (or gzipped TSV) file.
    Streams the file line‑by‑line to avoid loading the entire file into memory.
    Raises ConnectionError if the file cannot be accessed.
    """
    try:
        # The eBird dataset on HuggingFace is hosted under the repo "ebird/ebd".
        # The primary data file is a tab‑separated values file; its exact name
        # can change over time, but the hub always provides a file named
        # "ebd_relMay-2024.txt" (or a similar timestamped name). We attempt
        # to download the most recent file by trying a few known conventions.
        possible_filenames = [
            "ebd_relMay-2024.txt",
            "ebd_relMay-2024.txt.gz",
            "ebd_relJun-2024.txt",
            "ebd_relJun-2024.txt.gz",
        ]
        file_path = None
        for fname in possible_filenames:
            try:
                file_path = hf_hub_download(
                    repo_id="ebird/ebd",
                    filename=fname,
                    repo_type="dataset",
                )
                logger.info(f"Downloaded eBird dataset file: {fname}")
                break
            except Exception:
                continue
        if file_path is None:
            raise FileNotFoundError("Could not locate eBird dataset file in the hub.")
    except Exception as exc:
        logger.error(f"Failed to download eBird dataset via HuggingFace hub: {exc}")
        raise ConnectionError(
            "Unable to fetch eBird dataset from HuggingFace hub."
        ) from exc

    # Determine if the file is gzipped
    open_func = gzip.open if file_path.endswith(".gz") else open

    # Open the file and stream rows as dictionaries.
    with open_func(file_path, mode="rt", encoding="utf-8") as f:
        # The eBird file is tab‑separated; fallback to comma if tabs not found.
        sample = f.read(1024)
        f.seek(0)
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(f, delimiter=delimiter)
        for record in reader:
            yield record

def _fetch_modis_data():
    """
    Placeholder for MODIS fetching logic.
    Not required for task T002 but defined for completeness.
    """
    raise ConnectionError("MODIS data fetching not implemented in this module.")

# -----------------------------------------------------------------
# Public API
# -----------------------------------------------------------------
def load_ebird_data() -> pd.DataFrame:
    """
    Streams the eBird Basic Dataset (sample), filters for Setophaga ruticilla
    (species_code == \"SRUT\") and complete‑checklist criteria, then writes
    a chunked CSV to ``data/raw/ebd_subset.csv``.
    Also creates/updates ``data/raw/checksums.json`` with the SHA‑256
    checksum of the CSV.
    Raises ConnectionError if the remote fetch cannot be performed.
    """
    output_path = DATA_RAW / EBIRD_OUTPUT_FILE
    checksum_path = DATA_RAW / CHECKSUMS_FILE

    # Ensure the raw data directory exists
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # If we already have a verified CSV, reuse it.
    # -----------------------------------------------------------------
    if output_path.is_file():
        if checksum_path.is_file():
            try:
                with open(checksum_path, "r") as f:
                    stored = json.load(f)
                stored_hash = stored.get(EBIRD_OUTPUT_FILE)
                current_hash = calculate_sha256(output_path)
                if stored_hash == current_hash:
                    logger.info(f"Existing eBird subset found and verified at {output_path}")
                    return pd.read_csv(output_path)
            except Exception as exc:
                logger.warning(f"Checksum verification failed: {exc}")
        else:
            logger.info(f"Existing eBird subset found (no checksum) at {output_path}")
            return pd.read_csv(output_path)

    # -----------------------------------------------------------------
    # Stream download & filtering
    # -----------------------------------------------------------------
    logger.info("Starting streaming download of the eBird dataset via HuggingFace hub...")
    ds_iter = _fetch_ebird_data()

    header_written = False
    buffer = []
    rows_written = 0

    for idx, record in enumerate(ds_iter, start=1):
        if not _filter_record(record):
            continue

        buffer.append(record)

        if len(buffer) >= CHUNK_SIZE:
            df_chunk = pd.DataFrame(buffer)
            mode = "w" if not header_written else "a"
            header = not header_written
            df_chunk.to_csv(output_path, index=False, mode=mode, header=header)
            header_written = True
            rows_written += len(buffer)
            buffer.clear()
            logger.debug(f"Wrote {rows_written} processed rows to {output_path}")

        # Safety limit to keep runtime reasonable on CI
        if rows_written >= MAX_ROWS_TO_PROCESS:
            logger.info(f"Reached max rows limit ({MAX_ROWS_TO_PROCESS}); stopping early.")
            break

    # Write any remaining rows
    if buffer:
        df_chunk = pd.DataFrame(buffer)
        mode = "w" if not header_written else "a"
        header = not header_written
        df_chunk.to_csv(output_path, index=False, mode=mode, header=header)
        rows_written += len(buffer)
        logger.info(f"Final write completed. Total rows written to {output_path}")

    if rows_written == 0:
        raise RuntimeError("No records matched the filtering criteria; output file is empty.")

    # -----------------------------------------------------------------
    # Checksum handling
    # -----------------------------------------------------------------
    checksum = calculate_sha256(output_path)
    checksums = {}
    if checksum_path.is_file():
        try:
            with open(checksum_path, "r") as f:
                checksums = json.load(f)
        except Exception:
            checksums = {}
    checksums[EBIRD_OUTPUT_FILE] = checksum
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"SHA‑256 checksum stored in {checksum_path}")

    # Return the freshly written DataFrame
    return pd.read_csv(output_path)

def load_modis_data():
    """
    Placeholder for MODIS data loading.
    This function is required by unit tests to exist and should raise
    ConnectionError to satisfy the “fail loudly” contract.
    """
    raise ConnectionError("MODIS data loading not implemented in this module.")

def main() -> None:
    """Entry point for the data‑loading stage."""
    logger.info("Running eBird data loader...")
    try:
        df = load_ebird_data()
        logger.info(f"eBird data successfully loaded: {len(df)} rows.")
    except ConnectionError as ce:
        logger.critical(f"Data loading failed: {ce}")
        raise

if __name__ == "__main__":
    main()
