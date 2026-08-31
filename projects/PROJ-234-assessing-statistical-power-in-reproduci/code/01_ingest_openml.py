import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import from local utils as per API surface
from utils.logging_config import setup_logging

def filter_datasets(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter datasets to keep only those with a publication_link OR a task_id.
    """
    filtered = []
    for item in raw_data:
        if item.get('publication_link') or item.get('task_id'):
            filtered.append(item)
    return filtered

def deduplicate_datasets(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate for duplicate dataset_ids.
    Keep the entry with the highest download_count for each ID.
    Raises ValueError if duplicates remain after resolution (should not happen if logic is correct,
    but included for safety as per T016 requirement).
    """
    id_map: Dict[int, Dict[str, Any]] = {}

    for ds in datasets:
        ds_id = ds.get('dataset_id')
        if ds_id is None:
            continue  # Skip entries without ID

        if ds_id in id_map:
            existing = id_map[ds_id]
            # Compare download counts (default to 0 if missing)
            current_count = ds.get('download_count', 0)
            existing_count = existing.get('download_count', 0)

            if current_count > existing_count:
                id_map[ds_id] = ds
        else:
            id_map[ds_id] = ds

    # Final check for duplicates (should be empty set if logic holds)
    final_list = list(id_map.values())
    seen_ids = set()
    duplicates_found = []
    for item in final_list:
        if item['dataset_id'] in seen_ids:
            duplicates_found.append(item['dataset_id'])
        seen_ids.add(item['dataset_id'])

    if duplicates_found:
        raise ValueError(f"Duplicate dataset_ids remain after resolution: {duplicates_found}")

    return final_list

def generate_checksums(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate SHA-256 checksums for the dataset entries.
    Since the data is a list of dicts, we compute the hash of the
    canonical JSON representation (sorted keys, no extra whitespace).
    Writes a text file with format: <hash>  <dataset_id>
    """
    checksums = []
    for ds in data:
        # Canonical JSON string
        canonical_str = json.dumps(ds, sort_keys=True, separators=(',', ':'))
        digest = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()
        ds_id = ds.get('dataset_id', 'unknown')
        checksums.append(f"{digest}  {ds_id}")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(checksums))
        if checksums:
            f.write('\n')

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting OpenML ingestion and deduplication (T012-T014)")

    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / 'data' / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_file = raw_dir / 'openml_metadata_raw.json'
    filtered_file = raw_dir / 'openml_metadata_filtered.json'
    checksum_file = raw_dir / 'checksums.txt'

    # 1. Load raw data (assumed to exist from T012)
    if not raw_file.exists():
        logger.error(f"Raw data file not found: {raw_file}. Please run T012 first.")
        sys.exit(1)

    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    logger.info(f"Loaded {len(raw_data)} raw datasets.")

    # 2. Filter (T013 logic)
    filtered_data = filter_datasets(raw_data)
    logger.info(f"Filtered to {len(filtered_data)} datasets with publication_link or task_id.")

    # Save filtered data
    with open(filtered_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, indent=2)
    logger.info(f"Saved filtered data to {filtered_file}")

    # 3. Deduplicate and generate checksums (T014 logic)
    try:
        deduped_data = deduplicate_datasets(filtered_data)
        logger.info(f"Deduplicated to {len(deduped_data)} unique datasets.")
    except ValueError as e:
        logger.error(f"Deduplication failed: {e}")
        sys.exit(1)

    # Generate checksums
    generate_checksums(deduped_data, str(checksum_file))
    logger.info(f"Generated checksums written to {checksum_file}")

    logger.info("Ingestion and validation complete.")

if __name__ == '__main__':
    main()
