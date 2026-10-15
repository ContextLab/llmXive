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
from pathlib import Path
from typing import List, Dict, Any

# Project‑wide logging helper
from utils.logging_config import setup_logging

# API helper
from utils.api_client import fetch_top_classification_datasets

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
    """
    return [
        ds
        for ds in datasets
        if ds.get("publication_link") or ds.get("task_id")
    ]

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

    # 1. Fetch raw data
    try:
        raw_datasets = fetch_top_classification_datasets(limit=50)
    except Exception as exc:
        logger.error(f"Failed to fetch datasets from OpenML: {exc}")
        sys.exit(1)

    # Persist raw response
    save_json_file(RAW_OUTPUT, raw_datasets)
    logger.info(f"Saved raw OpenML metadata to {RAW_OUTPUT}")

    # 2. Filter
    filtered = filter_datasets(raw_datasets)
    save_json_file(FILTERED_OUTPUT, filtered)
    logger.info(f"Saved filtered dataset list to {FILTERED_OUTPUT}")

    # 3. Deduplicate (required by T014/T016)
    deduped = deduplicate_datasets(filtered)

    # Overwrite filtered output with deduplicated version
    save_json_file(FILTERED_OUTPUT, deduped)
    logger.info(
        f"Deduplicated filtered list now contains {len(deduped)} entries."
    )

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
        data_type = (ds.get("data_type") or "").lower()
        if "binary" in data_type:
            type_dist["binary"] += 1
        elif "multiclass" in data_type:
            type_dist["multiclass"] += 1

    log_extraction_statistics(len(raw_datasets), len(deduped), type_dist)
    logger.info("Ingestion process completed successfully.")

if __name__ == "__main__":
    main()