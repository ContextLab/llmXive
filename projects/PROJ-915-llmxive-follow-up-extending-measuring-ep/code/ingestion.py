"""
Data ingestion module: Download MedMisBench, filter subsets, and save with checksums.
Implements T013: Download MedMisBench, filter for specific labels, save to CSV, compute SHA-256.
"""
import os
import hashlib
import csv
import yaml
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset
import pandas as pd

from config import config
from error_handling import safe_download_with_retry, DatasetDownloadError
from validation import validate_data_integrity

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_and_filter_dataset(
    dataset_name: str,
    filter_labels: List[str],
    streaming: bool = True
) -> List[Dict[str, Any]]:
    """
    Load MedMisBench dataset and filter for specific labels.
    Uses streaming to handle large datasets efficiently.
    Fails loudly if download fails (no synthetic fallback).
    """
    logger.info(f"Loading dataset '{dataset_name}' with streaming={streaming}...")
    
    try:
        if streaming:
            dataset = load_dataset(dataset_name, streaming=True)
        else:
            dataset = load_dataset(dataset_name)
        
        filtered_data = []
        target_labels = set(filter_labels)
        
        # Determine splits (streaming datasets might not have explicit split keys initially)
        # We iterate over all available splits
        splits = list(dataset.keys()) if hasattr(dataset, 'keys') else [None]
        
        for split in splits:
            split_dataset = dataset[split] if split else dataset
            
            for item in split_dataset:
                # Check for label in various possible fields
                # MedMisBench typically uses 'label', 'category', or 'type'
                label_val = item.get('label', item.get('category', item.get('type', '')))
                
                # Check if any target label is in the value (case-insensitive partial match)
                label_str = str(label_val).lower()
                if any(target.lower() in label_str for target in target_labels):
                    filtered_data.append(item)
                    logger.debug(f"Filtered item: {item.get('id', 'no-id')} with label: {label_val}")
        
        if not filtered_data:
            logger.warning(f"No items found matching labels: {filter_labels}")
        
        return filtered_data
        
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_name}': {e}")
        # Re-raise as DatasetDownloadError to fail loudly
        raise DatasetDownloadError(f"Dataset download failed for '{dataset_name}': {e}")

def save_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """Save list of dicts to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        logger.warning("No data to save.")
        # Create empty file to indicate pipeline ran but found nothing
        output_path.touch()
        return
    
    # Flatten nested dicts if necessary
    def flatten(d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten(v, new_key, sep=sep).items())
            elif isinstance(v, (list, tuple)):
                # Convert lists to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    flattened_data = [flatten(item) for item in data]
    df = pd.DataFrame(flattened_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(data)} rows to {output_path}")

def update_hash_state(file_path: Path, state_file: Path):
    """Compute hash and update state file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    file_hash = compute_sha256(file_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    state = {}
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing state file: {e}. Starting fresh.")
            state = {}
    
    state[file_path.name] = {
        "hash": file_hash,
        "path": str(file_path),
        "timestamp": time.time()
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Updated hash state for {file_path.name} in {state_file}")
    logger.info(f"SHA-256: {file_hash}")

def run_ingestion_pipeline():
    """Main pipeline for ingestion."""
    logger.info("Starting ingestion pipeline...")
    
    # Configuration
    dataset_name = config.datasets.get("medmis_bench_name", "medmis-bench")
    filter_labels = config.datasets.get("subset_labels", ["Authority-framed", "Exception-poisoning"])
    output_path = Path(config.paths["data_raw"]) / "medmis_subset.csv"
    state_file = Path(config.paths["state"]) / "artifact_hashes.yaml"

    try:
        # Load and filter
        logger.info(f"Filtering for labels: {filter_labels}")
        data = load_and_filter_dataset(dataset_name, filter_labels)
        
        # Save
        save_to_csv(data, output_path)
        
        # Compute and save hash
        update_hash_state(output_path, state_file)
        
        logger.info("Ingestion pipeline completed successfully.")
        return True
    except DatasetDownloadError as e:
        logger.error(f"Dataset download failed (as expected if source unavailable): {e}")
        raise
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_ingestion_pipeline()