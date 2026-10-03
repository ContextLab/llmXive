"""
code/ingestion.py
Implements T013: Download MedMisBench, filter subsets, validate schema with regex fallback,
compute checksums, and save to CSV.
"""

import os
import hashlib
import csv
import yaml
import re
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Iterator

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' package is required. Install with: pip install datasets")

logger = logging.getLogger(__name__)

# Configuration
DATASET_NAME = "allenai/medmis-bench"
SPLIT = "train"
CHUNK_SIZE = 1000
FILTER_LABELS = ["Authority-framed", "Exception-poisoning"]

# Regex pattern for false_claim extraction fallback
FALSE_CLAIM_PATTERN = re.compile(r'false_claim\s*[:=]\s*([\'"]?[^\'",]+[\'"]?)')

def load_and_filter_dataset(dataset_name: str = DATASET_NAME, split: str = SPLIT) -> Iterator[Dict[str, Any]]:
    """
    Load MedMisBench dataset using streaming to avoid OOM.
    Filters for "Authority-framed" and "Exception-poisoning" labels.
    Returns an iterator to allow chunked processing.
    """
    logger.info(f"Loading dataset: {dataset_name} (streaming=True)")
    
    try:
        dataset = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Dataset download failed: {e}")

    for item in dataset:
        # Filter logic: Check for specific labels
        label = item.get('label', item.get('category', item.get('type', '')))
        if label in FILTER_LABELS:
            yield item

def validate_schema(item: Dict[str, Any]) -> Optional[str]:
    """
    Validate schema: Check for 'false_claim' column.
    If missing, attempt regex extraction fallback.
    Returns the false claim text if found/extracted, else raises error.
    """
    if 'false_claim' in item:
        return item['false_claim']

    # Fallback: Extract from text using regex
    # We need a text field to search. Common fields: 'prompt', 'question', 'text'
    text_fields = ['prompt', 'question', 'text', 'input']
    text_content = ""
    for field in text_fields:
        if field in item:
            text_content = str(item[field])
            break
    
    if not text_content:
        raise RuntimeError("Schema validation failed: No 'false_claim' column and no text content found for regex extraction.")

    match = FALSE_CLAIM_PATTERN.search(text_content)
    if match:
        extracted = match.group(1).strip().strip("'\"")
        logger.info(f"Extracted false_claim via regex: {extracted[:50]}...")
        return extracted
    
    # If extraction fails, abort with clear error (as per T013 spec)
    raise RuntimeError("Schema validation failed: 'false_claim' column missing and regex extraction fallback failed.")

def save_to_csv(data_iterator: Iterator[Dict[str, Any]], output_path: str) -> int:
    """Save filtered data to CSV in chunks. Returns row count."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    row_count = 0
    fieldnames = None
    writer = None

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        for item in data_iterator:
            # Ensure schema is valid before saving (extract false_claim if needed)
            try:
                false_claim_val = validate_schema(item)
                if false_claim_val:
                    item['false_claim'] = false_claim_val
            except RuntimeError as e:
                logger.error(f"Skipping row due to validation error: {e}")
                continue

            if fieldnames is None:
                fieldnames = list(item.keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

            writer.writerow(item)
            row_count += 1
            
            if row_count % CHUNK_SIZE == 0:
                logger.info(f"Saved {row_count} rows...")

    logger.info(f"Saved total {row_count} rows to {output_path}")
    return row_count

def save_checksum_to_state(output_path: str, state_path: str) -> None:
    """Compute SHA-256 checksum of the saved CSV and record in state file."""
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Output file not found for checksum: {output_path}")

    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()

    state_dir = os.path.dirname(state_path)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir)

    # Load existing state if exists, else create new
    existing_state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r') as sf:
                existing_state = yaml.safe_load(sf) or {}
        except Exception:
            existing_state = {}

    existing_state['medmis_subset_checksum'] = checksum
    existing_state['medmis_subset_file'] = output_path
    existing_state['timestamp'] = str(datetime.now())

    with open(state_path, 'w') as f:
        yaml.dump(existing_state, f)
    
    logger.info(f"Checksum saved to {state_path}: {checksum}")

def run_ingestion_pipeline() -> None:
    """Main ingestion pipeline."""
    output_path = 'data/raw/medmis_subset.csv'
    state_path = 'state/artifact_hashes.yaml'

    # Load and filter
    data_iterator = load_and_filter_dataset()
    
    try:
        row_count = save_to_csv(data_iterator, output_path)
    except RuntimeError as e:
        logger.error(f"Ingestion failed during save/validation: {e}")
        raise e

    if row_count == 0:
        raise RuntimeError("No data filtered. Aborting.")

    # Save checksum
    save_checksum_to_state(output_path, state_path)

    logger.info("Ingestion pipeline complete.")

def main() -> None:
    """CLI entry point."""
    try:
        run_ingestion_pipeline()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()