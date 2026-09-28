import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging configuration from the shared utility
from utils.logging_config import setup_logging

# Constants
RAW_DATA_DIR = Path("data/raw")
LOG_FILE = "data/ingest.log"
CHECKSUMS_FILE = RAW_DATA_DIR / "checksums.txt"
RAW_OUTPUT = RAW_DATA_DIR / "openml_metadata_raw.json"
FILTERED_OUTPUT = RAW_DATA_DIR / "openml_metadata_filtered.json"

def load_json_file(path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its content."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(path: Path, data: Any) -> None:
    """Save data to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
    """
    Fetch top classification datasets from OpenML.
    Delegates to the OpenMLClient utility for retry logic.
    """
    from utils.api_client import fetch_top_classification_datasets as fetch_datasets
    return fetch_datasets(limit=limit)

def filter_datasets(datasets: List[Dict]) -> List[Dict]:
    """
    Filter datasets that have a 'publication_link' OR a 'task_id'.
    """
    filtered = []
    for ds in datasets:
        if ds.get("publication_link") or ds.get("task_id"):
            filtered.append(ds)
    return filtered

def deduplicate_datasets(datasets: List[Dict]) -> List[Dict]:
    """
    Deduplicate datasets by 'dataset_id'.
    If duplicates exist, keep the entry with the highest 'download_count'.
    Raises ValueError if duplicates remain after resolution (T016).
    """
    id_map: Dict[int, Dict] = {}
    for ds in datasets:
        ds_id = ds.get("dataset_id")
        if ds_id is None:
            continue
        
        if ds_id in id_map:
            existing = id_map[ds_id]
            current_count = ds.get("download_count", 0)
            existing_count = existing.get("download_count", 0)
            if current_count > existing_count:
                id_map[ds_id] = ds
        else:
            id_map[ds_id] = ds

    result = list(id_map.values())
    
    # T016: Ensure no duplicate IDs remain; raise ValueError if any remain
    # (This is technically guaranteed by the logic above, but we assert for safety)
    seen_ids = set()
    for ds in result:
        ds_id = ds.get("dataset_id")
        if ds_id in seen_ids:
            raise ValueError(f"Duplicate dataset_id {ds_id} found after deduplication logic.")
        seen_ids.add(ds_id)
    
    return result

def generate_checksums(datasets: List[Dict], output_path: Path) -> None:
    """
    Generate SHA-256 checksums for each dataset entry and write to a file.
    Format: <sha256>  <dataset_id>
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for ds in datasets:
            ds_id = ds.get("dataset_id", "unknown")
            # Create a canonical string for hashing
            canonical = json.dumps(ds, sort_keys=True)
            checksum = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            f.write(f"{checksum}  {ds_id}\n")

def log_extraction_statistics(total_fetched: int, filtered: int, type_dist: Dict[str, int]) -> None:
    """
    Log extraction statistics to the ingest log file.
    """
    logger = setup_logging(LOG_FILE)
    stats = {
        "total_fetched": total_fetched,
        "filtered": filtered,
        "type_distribution": type_dist
    }
    logger.info(json.dumps(stats))

def main():
    """Main execution flow for US1."""
    # Setup logging
    logger = setup_logging(LOG_FILE)
    logger.info("Starting OpenML ingestion process.")

    # 1. Fetch raw data
    try:
        raw_datasets = fetch_top_classification_datasets(limit=50)
    except Exception as e:
        logger.error(f"Failed to fetch datasets: {e}")
        sys.exit(1)

    save_json_file(RAW_OUTPUT, raw_datasets)
    logger.info(f"Saved raw metadata to {RAW_OUTPUT}")

    # 2. Filter datasets
    filtered_datasets = filter_datasets(raw_datasets)
    save_json_file(FILTERED_OUTPUT, filtered_datasets)
    logger.info(f"Saved filtered metadata to {FILTERED_OUTPUT}")

    # 3. Deduplicate (T014 & T016)
    deduped_datasets = deduplicate_datasets(filtered_datasets)
    
    # 4. Generate checksums (T014)
    generate_checksums(deduped_datasets, CHECKSUMS_FILE)
    logger.info(f"Generated checksums at {CHECKSUMS_FILE}")

    # 5. Log statistics (T015)
    type_dist = {"binary": 0, "multiclass": 0}
    for ds in deduped_datasets:
        data_type = ds.get("data_type", "").lower()
        if "binary" in data_type:
            type_dist["binary"] += 1
        elif "multiclass" in data_type:
            type_dist["multiclass"] += 1
    
    log_extraction_statistics(len(raw_datasets), len(deduped_datasets), type_dist)
    logger.info("Ingestion process completed successfully.")

if __name__ == "__main__":
    main()
