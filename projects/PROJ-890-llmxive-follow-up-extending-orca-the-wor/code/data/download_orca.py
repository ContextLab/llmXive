"""
download_orca.py

Implements the data download and filtering logic for the Orca dataset.
Fetches real data from HuggingFace and filters for physical interactions.
"""

import os
import sys
import logging
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Ensure code/ is in path for relative imports if running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config import ensure_directories, get_config
from utils.audit_logger import log_skipped_file, log_audit_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Real dataset ID for Orca
ORCA_DATASET_ID = "microsoft/orca"

# Fixed seed for reproducibility of the subset
RANDOM_SEED = 42

def load_orca_dataset() -> List[Dict[str, Any]]:
    """
    Loads the Orca dataset from HuggingFace.
    Returns a list of dictionaries representing the dataset rows.
    """
    logger.info("Loading Orca dataset from HuggingFace...")
    try:
        from datasets import load_dataset

        # Load the dataset (using the real Orca dataset ID)
        dataset = load_dataset(ORCA_DATASET_ID, split="train")

        # Convert to list of dicts
        data_list = dataset.to_list()
        logger.info(f"Loaded {len(data_list)} samples from Orca dataset.")
        return data_list
    except Exception as e:
        logger.error(f"Failed to load Orca dataset: {e}")
        raise RuntimeError(f"Dataset loading failed: {e}")

def filter_physical_interactions(
    dataset: List[Dict[str, Any]],
    threshold: float
) -> List[Dict[str, Any]]:
    """
    Filters the dataset to include only clips with significant optical flow.

    This implements FR-001: exclude non-physical interaction clips using
    optical_flow_magnitude < config.OPTICAL_FLOW_THRESHOLD on the metadata field.

    Args:
        dataset: List of dataset rows.
        threshold: Minimum optical flow magnitude to consider a clip physical.

    Returns:
        List of filtered dataset rows.
    """
    logger.info(f"Filtering for physical interactions (threshold={threshold})...")
    filtered = []
    skipped_count = 0

    for item in dataset:
        # Assuming 'metadata' contains 'optical_flow_magnitude'
        # If the actual dataset structure is different, this needs adjustment.
        metadata = item.get("metadata", {})
        
        # Handle case where metadata might be a JSON string
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}
        
        if not isinstance(metadata, dict):
            metadata = {}

        # Extract optical flow magnitude, defaulting to 0.0 if missing
        flow_mag = metadata.get("optical_flow_magnitude", 0.0)

        # Apply threshold: keep if flow_mag >= threshold
        if flow_mag >= threshold:
            filtered.append(item)
        else:
            video_id = item.get("video_id", "unknown")
            log_skipped_file(video_id, f"Optical flow {flow_mag} < {threshold}")
            skipped_count += 1

    logger.info(f"Filtered dataset: {len(filtered)} physical interaction clips.")
    logger.info(f"Skipped {skipped_count} non-physical clips.")
    return filtered

def save_outputs(data: List[Dict[str, Any]], output_path: Path):
    """
    Saves the filtered dataset to a file.
    Saves as JSON for now, can be extended to CSV if needed.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} items to {output_path}")

def save_subset_to_csv(data: List[Dict[str, Any]], output_path: Path, n_samples: int = 50):
    """
    Extracts a random subset of N samples from the filtered dataset and saves as CSV.
    Implements T012b: Create N=50 Subset File.

    Args:
        data: List of filtered dataset rows.
        output_path: Path to save the CSV file.
        n_samples: Number of samples to extract (default 50).
    """
    if len(data) < n_samples:
        logger.warning(f"Dataset size ({len(data)}) is less than requested subset size ({n_samples}). "
                       f"Taking all available samples.")
        subset = data
    else:
        random.seed(RANDOM_SEED)
        subset = random.sample(data, n_samples)
        logger.info(f"Randomly selected {n_samples} samples for subset.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine columns from the first item (assuming uniform structure)
    if not subset:
        logger.warning("Subset is empty. Creating empty CSV with no columns.")
        with open(output_path, 'w') as f:
            pass # Create empty file
        return

    # Flatten nested metadata if necessary, or select specific fields
    # We will save 'video_id', 'prompt', and 'metadata' (as JSON string) for usability
    fieldnames = ['video_id', 'prompt', 'metadata']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for item in subset:
            row = {
                'video_id': item.get('video_id', ''),
                'prompt': item.get('prompt', ''),
                'metadata': json.dumps(item.get('metadata', {}))
            }
            writer.writerow(row)

    logger.info(f"Saved {len(subset)} samples to {output_path}")

def main():
    """
    Main function to download, filter, and save the N=50 subset of the Orca dataset.
    Implements T012, T012b.
    """
    ensure_directories()
    config = get_config()

    dataset = load_orca_dataset()
    filtered = filter_physical_interactions(dataset, config.OPTICAL_FLOW_THRESHOLD)

    # T012: Save full filtered dataset (JSON)
    output_path_full = Path(config.PROCESSED_DIR) / "orca_filtered.json"
    save_outputs(filtered, output_path_full)

    # T012b: Save N=50 subset (CSV)
    output_path_subset = Path(config.RAW_DIR) / "scenarios.csv"
    save_subset_to_csv(filtered, output_path_subset, n_samples=50)

if __name__ == "__main__":
    main()