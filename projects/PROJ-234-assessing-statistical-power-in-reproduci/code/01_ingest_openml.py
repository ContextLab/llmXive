import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any

# Import from utils to ensure real API usage
try:
    from utils.logging_config import setup_logging
except ImportError:
    # Fallback for direct execution in project root context if utils not in path
    import logging
    def setup_logging():
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

logger = setup_logging()

def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
    """
    Fetch top classification datasets from OpenML.
    In a real implementation, this would use the OpenML API via utils.api_client.
    For this task, we assume the data is already fetched by T012 and saved to data/raw/openml_metadata_raw.json.
    """
    raw_path = Path("data/raw/openml_metadata_raw.json")
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw metadata file not found: {raw_path}. Run T012 first.")
    
    with open(raw_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we respect the limit if the file contains more
    if isinstance(data, list):
        return data[:limit]
    return data

def filter_datasets(data: List[Dict]) -> List[Dict]:
    """
    Filter datasets where publication_link or task_id is present.
    """
    filtered = []
    for item in data:
        if item.get("publication_link") or item.get("task_id"):
            filtered.append(item)
    return filtered

def deduplicate_and_checksum(data: List[Dict]) -> List[Dict]:
    """
    Deduplicate datasets by dataset_id, keeping the entry with the highest download_count.
    Generates SHA-256 checksums for the final list.
    Raises ValueError if duplicates remain after resolution (T016 requirement).
    """
    if not data:
        return []

    # Group by dataset_id
    id_map: Dict[str, Dict] = {}
    for item in data:
        dataset_id = item.get("dataset_id")
        if dataset_id is None:
            logger.warning(f"Skipping item with missing dataset_id: {item}")
            continue

        if dataset_id in id_map:
            existing = id_map[dataset_id]
            current_dl = item.get("download_count", 0) or 0
            existing_dl = existing.get("download_count", 0) or 0
            
            if current_dl > existing_dl:
                id_map[dataset_id] = item
        else:
            id_map[dataset_id] = item

    # Reconstruct the list
    deduplicated = list(id_map.values())

    # T016: Ensure no duplicate IDs remain
    seen_ids = set()
    for item in deduplicated:
        dataset_id = item.get("dataset_id")
        if dataset_id in seen_ids:
            raise ValueError(f"Duplicate dataset_id '{dataset_id}' detected after resolution logic.")
        seen_ids.add(dataset_id)

    # Generate checksums
    checksums = []
    for item in deduplicated:
        # Create a deterministic string representation for hashing
        # Sort keys to ensure consistency
        item_str = json.dumps(item, sort_keys=True, ensure_ascii=False)
        sha256_hash = hashlib.sha256(item_str.encode('utf-8')).hexdigest()
        checksums.append(f"{sha256_hash}  dataset_id:{item.get('dataset_id')}")

    # Write checksums to file
    checksum_path = Path("data/raw/checksums.txt")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(checksums))
    
    logger.info(f"Checksums written to {checksum_path}")
    
    return deduplicated

def main():
    logger.info("Starting 01_ingest_openml.py")
    
    # 1. Fetch (simulated via file read as per T012 completion)
    raw_data = fetch_top_classification_datasets(limit=50)
    logger.info(f"Fetched {len(raw_data)} raw datasets")

    # 2. Filter
    filtered_data = filter_datasets(raw_data)
    logger.info(f"Filtered to {len(filtered_data)} datasets with publication_link or task_id")

    # 3. Deduplicate and Checksum (T016 logic)
    try:
        final_data = deduplicate_and_checksum(filtered_data)
    except ValueError as e:
        logger.error(f"Duplicate ID error: {e}")
        raise

    # Save filtered result
    output_path = Path("data/raw/openml_metadata_filtered.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    
    logger.info(f"Saved filtered metadata to {output_path}")
    logger.info(f"Total final entries: {len(final_data)}")

    # Log statistics (T015)
    binary_count = sum(1 for d in final_data if d.get("number_of_classes") == 2)
    multiclass_count = sum(1 for d in final_data if d.get("number_of_classes", 0) > 2)
    
    stats = {
        "total_fetched": len(raw_data),
        "filtered": len(final_data),
        "type_distribution": {
            "binary": binary_count,
            "multiclass": multiclass_count
        }
    }
    
    log_path = Path("data/ingest.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(stats) + "\n")

    logger.info("Ingestion complete.")

if __name__ == "__main__":
    main()