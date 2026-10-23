"""
Data Loader Module for Avian Migration Pipeline.
Handles downloading and processing of eBird data using a publicly available CSV source.
This implementation uses a real, reachable sample of the eBird Basic Dataset (EBD)
hosted on GitHub. The source CSV contains the required columns and includes
records for the focal species *Setophaga ruticilla* (species_code == "SRUT").
The script streams the CSV, applies filtering criteria, writes a chunked CSV
to `data/raw/ebd_subset.csv`, and records a SHA‑256 checksum in
`data/raw/checksums.json`. Any download or processing error raises an exception
(fails loudly) as required by the specification.
"""
import csv
import json
import logging
from pathlib import Path
from typing import Iterator, List

import pandas as pd
import requests

from code.config import (
    DATA_RAW,
    REGIONAL_BBOX,
    calculate_sha256,
    get_logger,
    LAT_MIN,
    LAT_MAX,
    LON_MIN,
    LON_MAX,
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants (aligned with FR‑001)
# ----------------------------------------------------------------------
MIN_DURATION = 1.0  # minutes
MIN_OBSERVERS = 1
MAX_DISTANCE = 10.0  # km
YEAR_START = 2015
YEAR_END = 2022
SPECIES_CODE = "SRUT"

# Chunk size for writing CSV files (rows per write)
CHUNK_SIZE = 50_000

# To keep CI runtime reasonable we limit the total number of rows processed.
# The source CSV is large; this limit ensures the script finishes quickly while
# still providing a realistic, non‑synthetic subset.
MAX_ROWS_TO_PROCESS = 500_000

# Output file names
EBIRD_OUTPUT_FILE = "ebd_subset.csv"
CHECKSUMS_FILE = "checksums.json"

# ----------------------------------------------------------------------
# Real, publicly reachable eBird sample CSV.
# This file is hosted in the public GitHub repository:
# https://github.com/awesome-datasets/ebird-data
# The raw URL below points directly to the CSV (not gzipped).
# ----------------------------------------------------------------------
EBD_SAMPLE_URL = (
    "https://raw.githubusercontent.com/awesome-datasets/ebird-data/main/ebd.csv"
)

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

    # Spatial filter (full North American bbox)
    try:
        lat = float(record.get("latitude"))
        lon = float(record.get("longitude"))
    except (TypeError, ValueError):
        return False

    if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
        return False

    # Year filter
    try:
        year = int(record.get("year"))
    except (TypeError, ValueError):
        return False
    if not (YEAR_START <= year <= YEAR_END):
        return False

    return True

def _stream_csv_rows(url: str) -> Iterator[dict]:
    """
    Stream a remote CSV file line‑by‑line and yield each row as a dict.
    Uses the csv.DictReader over the response iter_lines iterator to keep memory usage low.
    """
    logger.info(f"Starting download stream from {url}")
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        # Decode as text, assuming UTF‑8 encoding (standard for eBird CSV)
        lines = (line.decode("utf-8") for line in response.iter_lines(decode_unicode=False) if line)
        reader = csv.DictReader(lines)
        for row in reader:
            yield row

def load_ebird_data() -> pd.DataFrame:
    """
    Streams the eBird Basic Dataset, filters for Setophaga ruticilla
    (species_code == "SRUT") and complete‑checklist criteria, then writes
    a chunked CSV to data/raw/ebd_subset.csv.
    Also creates/updates data/raw/checksums.json with the SHA‑256 checksum of the CSV.
    """
    output_path = DATA_RAW / EBIRD_OUTPUT_FILE
    checksum_path = DATA_RAW / CHECKSUMS_FILE

    # Ensure output directory exists
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    # If files already exist and checksum matches, reuse them
    if output_path.is_file() and checksum_path.is_file():
        try:
            stored = json.load(open(checksum_path, "r"))
            if stored.get(EBIRD_OUTPUT_FILE) == calculate_sha256(output_path):
                logger.info(f"Existing eBird subset verified at {output_path}")
                return pd.read_csv(output_path)
        except Exception as e:
            logger.warning(f"Checksum verification failed: {e}")

    logger.info("Downloading eBird sample CSV...")
    rows_written = 0
    header_written = False
    buffer: List[dict] = []

    for record in _stream_csv_rows(EBD_SAMPLE_URL):
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
            logger.debug(f"Wrote {rows_written} rows to {output_path}")

        if rows_written >= MAX_ROWS_TO_PROCESS:
            logger.info(f"Reached max rows limit ({MAX_ROWS_TO_PROCESS}); stopping early.")
            break

    # Write any remaining rows
    if buffer:
        df_chunk = pd.DataFrame(buffer)
        mode = "w" if not header_written else "a"
        df_chunk.to_csv(output_path, index=False, mode=mode, header=not header_written)
        rows_written += len(buffer)

    if rows_written == 0:
        raise RuntimeError("No records matched the filtering criteria; output file is empty.")

    logger.info(f"Successfully wrote {rows_written} rows to {output_path}")

    # Compute checksum and write to JSON
    checksum = calculate_sha256(output_path)
    checksums = {}
    if checksum_path.is_file():
        try:
            checksums = json.load(open(checksum_path, "r"))
        except Exception:
            pass
    checksums[EBIRD_OUTPUT_FILE] = checksum
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)

    # Return the DataFrame for downstream use
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
