"""
OpenML Dataset Ingestion Script (US1).

Tasks:
- T012: Fetch top classification datasets.
- T013: Filter for publication_link or task_id.
- T014: Deduplicate by dataset_id (keep highest download_count) and generate checksums.
- T015: Log statistics.
"""
import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import from local utils as per API surface
from utils.api_client import fetch_top_classification_datasets
from utils.logging_config import setup_logging

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logger = setup_logging()


def filter_datasets(
    datasets: List[Dict[str, Any]], 
    required_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    T013: Filter datasets to keep only those with 'publication_link' OR 'task_id'.
    """
    filtered = []
    for ds in datasets:
        has_link = ds.get("publication_link") is not None and ds.get("publication_link") != ""
        has_task = ds.get("task_id") is not None
        
        if has_link or has_task:
            filtered.append(ds)
    
    logger.info(f"Filtered {len(datasets)} to {len(filtered)} datasets based on publication_link/task_id.")
    return filtered


def deduplicate_datasets(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T014: Validate for duplicate dataset_ids.
    Keep the entry with the highest download_count.
    """
    if not datasets:
        return []

    # Group by dataset_id
    id_groups = defaultdict(list)
    for ds in datasets:
        ds_id = ds.get("dataset_id")
        if ds_id is None:
            logger.warning("Found dataset with missing dataset_id, skipping.")
            continue
        id_groups[ds_id].append(ds)

    resolved = []
    duplicates_found = False

    for ds_id, group in id_groups.items():
        if len(group) > 1:
            duplicates_found = True
            # Sort by download_count descending (handle None as 0)
            group.sort(
                key=lambda x: x.get("download_count") or 0, 
                reverse=True
            )
            winner = group[0]
            logger.info(f"Duplicate dataset_id {ds_id} found ({len(group)} entries). Keeping highest download_count.")
        
        resolved.append(group[0])

    if duplicates_found:
        logger.info(f"Deduplication complete. Removed {len(datasets) - len(resolved)} duplicates.")
    else:
        logger.info("No duplicate dataset_ids found.")

    return resolved


def generate_checksums(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    T014: Generate SHA-256 checksums for the filtered/deduplicated JSON content.
    Writes a single checksum for the serialized JSON file content.
    """
    # Serialize to JSON with sorted keys for deterministic output
    json_str = json.dumps(data, sort_keys=True, indent=2)
    content_bytes = json_str.encode('utf-8')
    
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()
    
    # Write to checksum file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"{sha256_hash}  openml_metadata_filtered.json\n")
    
    logger.info(f"Checksum generated: {sha256_hash} -> {output_path}")


def main():
    """
    Main execution flow for T012, T013, T014, T015.
    """
    logger.info("Starting OpenML Ingestion Pipeline (US1).")

    # T012: Fetch
    raw_datasets = fetch_top_classification_datasets(limit=50)
    
    if not raw_datasets:
        logger.error("No datasets fetched from OpenML. Aborting.")
        sys.exit(1)

    raw_output = DATA_RAW_DIR / "openml_metadata_raw.json"
    with open(raw_output, 'w', encoding='utf-8') as f:
        json.dump(raw_datasets, f, indent=2, default=str)
    logger.info(f"Raw data saved to {raw_output}")

    # T013: Filter
    filtered_datasets = filter_datasets(raw_datasets)
    
    if not filtered_datasets:
        logger.error("No datasets passed the filter (publication_link or task_id). Aborting.")
        sys.exit(1)

    # T014: Deduplicate
    final_datasets = deduplicate_datasets(filtered_datasets)

    # Save filtered/deduplicated data
    filtered_output = DATA_RAW_DIR / "openml_metadata_filtered.json"
    with open(filtered_output, 'w', encoding='utf-8') as f:
        json.dump(final_datasets, f, indent=2, default=str)
    logger.info(f"Filtered/Deduplicated data saved to {filtered_output}")

    # T014: Checksums
    checksum_path = DATA_RAW_DIR / "checksums.txt"
    generate_checksums(final_datasets, checksum_path)

    # T015: Log Statistics (JSON format)
    type_dist = {"binary": 0, "multiclass": 0, "other": 0}
    for ds in final_datasets:
        # Assuming 'NumberOfClasses' or similar key exists in OpenML response
        n_classes = ds.get("NumberOfClasses")
        if n_classes is not None:
            if n_classes == 2:
                type_dist["binary"] += 1
            elif n_classes > 2:
                type_dist["multiclass"] += 1
            else:
                type_dist["other"] += 1
        else:
            type_dist["other"] += 1

    stats = {
        "total_fetched": len(raw_datasets),
        "filtered": len(final_datasets),
        "type_distribution": type_dist
    }
    
    # Append to ingest.log as JSON line (or overwrite for simplicity as requested)
    # The task asks to log extraction statistics as JSON to data/ingest.log
    log_stats_path = PROJECT_ROOT / "data" / "ingest.log"
    with open(log_stats_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(stats) + "\n")
    
    logger.info(f"Statistics logged to {log_stats_path}")
    logger.info(f"Pipeline complete. Output: {filtered_output}, Checksum: {checksum_path}")


if __name__ == "__main__":
    main()
