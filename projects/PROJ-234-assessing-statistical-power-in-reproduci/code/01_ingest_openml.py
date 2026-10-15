"""
code/01_ingest_openml.py
-------------------------

Implements the ingestion step (User Story 1):
1. Fetch the top 50 most‑downloaded classification datasets from OpenML.
2. Filter for entries that have a non‑null ``publication_link`` or ``task_id``.
3. Persist the raw response and the filtered list.
4. Produce SHA‑256 checksums for both persisted files and append them to a
   checksum manifest.
5. Write a short log with totals.

All output locations follow the specification in ``tasks.md``.
"""

import json
import sys
import hashlib
import os
from pathlib import Path
from typing import List, Dict, Any

import openml
from openml import config as openml_config
import pandas as pd

# Project‑wide logging helper
from utils.logging_config import setup_logging

# ----------------------------------------------------------------------
# Configure OpenML to use a writable cache directory inside the project.
# This avoids permission errors when the runner's home directory is not
# writable.
# ----------------------------------------------------------------------
openml_cache_dir = Path("data") / "openml_cache"
openml_cache_dir.mkdir(parents=True, exist_ok=True)
openml_config.cache_directory = str(openml_cache_dir)
# Ensure no API key is required for public metadata queries.
openml_config.apikey = None

# ----------------------------------------------------------------------
# Constants – paths are anchored to the repository root.
# ----------------------------------------------------------------------
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
LOG_FILE = Path("data/ingest.log")
CHECKSUM_MANIFEST = PROCESSED_DATA_DIR / "checksum_manifest.json"

RAW_OUTPUT = RAW_DATA_DIR / "openml_metadata_raw.json"
FILTERED_OUTPUT = PROCESSED_DATA_DIR / "filtered_datasets.json"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_json_file(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its content."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(path: Path, data: Any) -> None:
    """Save data to a JSON file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def filter_datasets(datasets: List[Dict]) -> List[Dict]:
    """
    Keep datasets that have a non‑null ``publication_link`` **or** ``task_id``.
    The OpenML listing does not always contain a dedicated ``publication_link``
    field; we treat the dataset ``url`` (the OpenML web page) as a proxy for a
    publication link when it is present.
    """
    filtered = []
    for ds in datasets:
        if ds.get("url") or ds.get("task_id"):
            filtered.append(ds)
    return filtered

def deduplicate_datasets(datasets: List[Dict]) -> List[Dict]:
    """
    Deduplicate by ``dataset_id`` – keep the entry with the highest
    ``download_count``.
    """
    id_map: Dict[int, Dict] = {}
    for ds in datasets:
        ds_id = ds.get("dataset_id")
        if ds_id is None:
            continue
        if ds_id in id_map:
            if ds.get("download_count", 0) > id_map[ds_id].get("download_count", 0):
                id_map[ds_id] = ds
        else:
            id_map[ds_id] = ds
    # Safety check – should never raise if logic is correct
    if len(id_map) != len(set(id_map)):
        raise ValueError("Duplicate dataset_id detected after deduplication.")
    return list(id_map.values())

def compute_file_checksum(path: Path) -> str:
    """Return the SHA‑256 checksum of a file's contents."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def append_to_checksum_manifest(entries: List[Dict[str, str]]) -> None:
    """
    Append checksum entries to ``checksum_manifest.json``.
    The manifest is a JSON list; if the file does not exist, start a new list.
    Each entry contains:
        {"file": "<relative path>", "sha256": "<hash>"}
    """
    CHECKSUM_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if CHECKSUM_MANIFEST.exists():
        with CHECKSUM_MANIFEST.open("r", encoding="utf-8") as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError:
                manifest = []
    else:
        manifest = []

    if not isinstance(manifest, list):
        manifest = []

    manifest.extend(entries)

    with CHECKSUM_MANIFEST.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def log_extraction_statistics(total_fetched: int, filtered: int, type_dist: Dict[str, int]) -> None:
    """
    Write a JSON line with simple statistics to the ingest log.
    """
    logger = setup_logging(str(LOG_FILE))
    stats = {
        "total_fetched": total_fetched,
        "filtered": filtered,
        "type_distribution": type_dist,
    }
    logger.info(json.dumps(stats))

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logging(str(LOG_FILE))
    logger.info("Starting OpenML ingestion process.")

    # 1. Fetch raw data – we request the full dataset list and then take the
    #    50 most‑downloaded classification datasets.
    try:
        # Retrieve the full OpenML dataset catalogue as a pandas DataFrame.
        df = openml.datasets.list_datasets(output_format="dataframe")
    except Exception as exc:
        logger.error(f"Failed to fetch datasets from OpenML: {exc}")
        sys.exit(1)

    # Keep only classification tasks.  OpenML marks the type in the
    # ``type`` column (e.g., "Supervised Classification").
    if "type" in df.columns:
        df = df[df["type"] == "Supervised Classification"]
    else:
        logger.warning("OpenML dataset list missing 'type' column; using full list.")

    # Sort by download count descending and take the top 50.
    if "download_count" in df.columns:
        df = df.sort_values(by="download_count", ascending=False).head(50)
    else:
        logger.warning("OpenML dataset list missing 'download_count' column; using unsorted list.")
        df = df.head(50)

    # Convert to a list of plain dictionaries.
    raw_datasets = df.to_dict(orient="records")

    # Normalise field names to match the contract where possible.
    for ds in raw_datasets:
        # Rename OpenML's primary identifier to ``dataset_id``.
        if "did" in ds:
            ds["dataset_id"] = ds.pop("did")
        # Use the OpenML web page URL as a proxy for ``publication_link``.
        if "url" in ds:
            ds["publication_link"] = ds["url"]
        # Preserve any existing ``task_id`` if present; otherwise leave as None.
        ds.setdefault("task_id", None)

    # Persist raw response
    save_json_file(RAW_OUTPUT, raw_datasets)
    logger.info(f"Saved raw OpenML metadata to {RAW_OUTPUT}")

    # 2. Filter
    filtered = filter_datasets(raw_datasets)
    save_json_file(FILTERED_OUTPUT, filtered)
    logger.info(f"Saved filtered dataset list to {FILTERED_OUTPUT}")

    # 3. Deduplicate (required by later tasks)
    deduped = deduplicate_datasets(filtered)

    # Overwrite filtered output with deduplicated version
    save_json_file(FILTERED_OUTPUT, deduped)
    logger.info(f"Deduplicated filtered list now contains {len(deduped)} entries.")

    # 4. Compute checksums for the two output files
    raw_checksum = compute_file_checksum(RAW_OUTPUT)
    filtered_checksum = compute_file_checksum(FILTERED_OUTPUT)

    checksum_entries = [
        {"file": str(RAW_OUTPUT), "sha256": raw_checksum},
        {"file": str(FILTERED_OUTPUT), "sha256": filtered_checksum},
    ]
    append_to_checksum_manifest(checksum_entries)
    logger.info(f"Appended checksums to {CHECKSUM_MANIFEST}")

    # 5. Log summary statistics
    type_dist = {"binary": 0, "multiclass": 0}
    for ds in deduped:
        # Determine binary vs multiclass from the number of classes if available.
        n_classes = ds.get("NumberOfClasses") or ds.get("nr_of_classes")
        if isinstance(n_classes, (int, float)):
            if n_classes == 2:
                type_dist["binary"] += 1
            elif n_classes > 2:
                type_dist["multiclass"] += 1

    log_extraction_statistics(len(raw_datasets), len(deduped), type_dist)
    logger.info("Ingestion process completed successfully.")

if __name__ == "__main__":
    main()
