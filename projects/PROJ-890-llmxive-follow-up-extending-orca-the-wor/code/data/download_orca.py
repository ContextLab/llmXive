"""
download_orca.py

Implements the data download and filtering logic for the Orca dataset.
Fetches real data from HuggingFace and filters for physical interactions.
"""

import os
import sys
import logging
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

def load_orca_dataset() -> List[Dict[str, Any]]:
    """
    Loads the Orca dataset from HuggingFace.
    Returns a list of dictionaries representing the dataset rows.
    """
    logger.info("Loading Orca dataset from HuggingFace...")
    try:
        from datasets import load_dataset

        # Load the dataset (using a placeholder dataset ID, replace with actual Orca dataset ID)
        # Note: The actual Orca dataset ID should be used here.
        dataset = load_dataset("microsoft/orca", split="train")

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

    Args:
        dataset: List of dataset rows.
        threshold: Minimum optical flow magnitude to consider a clip physical.

    Returns:
        List of filtered dataset rows.
    """
    logger.info(f"Filtering for physical interactions (threshold={threshold})...")
    filtered = []

    for item in dataset:
        # Assuming 'metadata' contains 'optical_flow_magnitude'
        flow_mag = item.get("metadata", {}).get("optical_flow_magnitude", 0.0)

        if flow_mag >= threshold:
            filtered.append(item)
        else:
            log_skipped_file(item.get("video_id", "unknown"), f"Optical flow {flow_mag} < {threshold}")

    logger.info(f"Filtered dataset: {len(filtered)} physical interaction clips.")
    return filtered

def save_outputs(data: List[Dict[str, Any]], output_path: Path):
    """
    Saves the filtered dataset to a file.
    For now, this is a placeholder for future CSV/JSON output logic.
    """
    import json
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} items to {output_path}")

def main():
    """
    Main function to download and filter the Orca dataset.
    """
    ensure_directories()
    config = get_config()

    dataset = load_orca_dataset()
    filtered = filter_physical_interactions(dataset, config.OPTICAL_FLOW_THRESHOLD)

    output_path = Path(config.PROCESSED_DIR) / "orca_filtered.json"
    save_outputs(filtered, output_path)

if __name__ == "__main__":
    main()