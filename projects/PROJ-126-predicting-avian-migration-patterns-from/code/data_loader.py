"""
Data Loader Module for Avian Migration Pipeline.
Handles downloading and processing of eBird data.
"""
import json
import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from config import DATA_RAW, REGIONAL_BBOX, get_logger

logger = get_logger(__name__)

# Constants for eBird filtering
MIN_DURATION = 1.0  # minutes
MIN_OBSERVERS = 1
MAX_DISTANCE = 10.0  # km

CHUNK_SIZE = 50_000  # rows per CSV write chunk

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
    if record.get("duration_min", 0) < MIN_DURATION:
        return False
    if record.get("num_observers", 0) < MIN_OBSERVERS:
        return False
    if record.get("distance_km", float("inf")) > MAX_DISTANCE:
        return False

    # Spatial filter (REGIONAL_BBOX)
    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is None or lon is None:
        return False
    min_lat, max_lat, min_lon, max_lon = REGIONAL_BBOX
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
        return False

    # Year filter
    year = record.get("year")
    if year is None or not (2015 <= year <= 2022):
        return False

    return True

def load_ebird_data() -> pd.DataFrame:
    """
    Streams the eBird Basic Dataset, filters for Setophaga ruticilla
    (species_code == "SRUT") and complete‑checklist criteria, then writes
    a chunked CSV to ``data/raw/ebd_subset.csv``.
    Also creates/updates ``data/raw/checksums.json`` with the SHA‑256
    checksum of the CSV.
    Raises ConnectionError if the remote fetch cannot be performed.
    """
    output_path = DATA_RAW / "ebd_subset.csv"
    checksum_path = DATA_RAW / "checksums.json"

    # If the CSV already exists and its checksum matches the stored value,
    # simply load and return it.
    if output_path.is_file():
        if checksum_path.is_file():
            try:
                with open(checksum_path, "r") as f:
                    stored = json.load(f)
                stored_hash = stored.get("ebd_subset.csv")
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
    logger.info("Starting streaming download of the eBird dataset...")
    try:
        # This will raise an exception if the dataset cannot be reached.
        ds = load_dataset("ebird/ebd", split="train", streaming=True)
    except Exception as exc:
        logger.error(f"Failed to stream eBird dataset: {exc}")
        raise ConnectionError(f"Unable to fetch eBird data: {exc}") from exc

    # Prepare CSV writing
    header_written = False
    buffer = []

    for idx, record in enumerate(ds, start=1):
        if not _filter_record(record):
            continue

        buffer.append(record)

        # When buffer reaches CHUNK_SIZE, write to CSV
        if len(buffer) >= CHUNK_SIZE:
            df_chunk = pd.DataFrame(buffer)
            mode = "w" if not header_written else "a"
            header = not header_written
            df_chunk.to_csv(output_path, index=False, mode=mode, header=header)
            header_written = True
            buffer.clear()
            logger.debug(f"Wrote {idx} processed rows to {output_path}")

    # Write any remaining rows
    if buffer:
        df_chunk = pd.DataFrame(buffer)
        mode = "w" if not header_written else "a"
        header = not header_written
        df_chunk.to_csv(output_path, index=False, mode=mode, header=header)
        logger.info(f"Final write completed. Total rows written to {output_path}")

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
    checksums["ebd_subset.csv"] = checksum
    with open(checksum_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"SHA‑256 checksum stored in {checksum_path}")

    # Return the freshly written DataFrame
    return pd.read_csv(output_path)

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