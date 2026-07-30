import logging
import json
import hashlib
import os
import signal
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

# Custom exception for augmentation timeouts
class AugmentationTimeoutError(Exception):
    pass

def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_processed_polyester_dataset(path: str) -> pd.DataFrame:
    """Load the processed dataset from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed dataset not found at {path}")
    return pd.read_csv(path)

def subsample_dataset(df: pd.DataFrame, target_size: int, seed: int = 42) -> pd.DataFrame:
    """
    Subsample the dataset to a specific target size.
    If the dataset is smaller than target_size, returns the original dataframe.
    """
    if len(df) <= target_size:
        return df
    
    logger = get_logger(__name__)
    logger.info(f"Subsampling dataset from {len(df)} to {target_size} records.")
    return df.sample(n=target_size, random_state=seed).reset_index(drop=True)

def save_dataset(df: pd.DataFrame, output_path: str, checksum_path: Optional[str] = None) -> None:
    """
    Save a dataset to CSV and optionally generate a checksum file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df.to_csv(output_path, index=False)
    logger = get_logger(__name__)
    logger.info(f"Saved dataset to {output_path} with {len(df)} records.")

    if checksum_path:
        checksum = compute_checksum(output_path)
        with open(checksum_path, "w") as f:
            json.dump({"path": output_path, "checksum": checksum}, f, indent=2)
        logger.info(f"Saved checksum to {checksum_path}: {checksum}")

def check_augmentation_trigger(trigger_path: str) -> Optional[Dict[str, Any]]:
    """
    Check if an augmentation trigger file exists.
    Returns the trigger config if present, None otherwise.
    """
    if os.path.exists(trigger_path):
        with open(trigger_path, "r") as f:
            return json.load(f)
    return None

def main():
    """
    Main entry point for T019: Data Saving.
    
    Logic:
    1. Check if augmentation was triggered (state/augmentation_trigger.json).
       - If triggered (50 <= n <= 150): Skip saving here (T016c is the pre-augmented source).
       - If NOT triggered (n > 150 or n < 50): 
         a. Load the subsampled dataset (from T018: data/processed/subsampled_polyesters.csv).
         b. Save it to data/processed/final_dataset.csv with checksums.
    """
    logger = setup_logging()
    paths = get_project_paths()
    
    trigger_path = paths["state"] / "augmentation_trigger.json"
    subsampled_path = paths["data_processed"] / "subsampled_polyesters.csv"
    final_output_path = paths["data_processed"] / "final_dataset.csv"
    checksum_path = paths["data_processed"] / "final_dataset.csv.sha256"

    # Check if augmentation was triggered
    trigger = check_augmentation_trigger(str(trigger_path))

    if trigger and trigger.get("action") == "augment":
        logger.info("Augmentation was triggered. Skipping final dataset save here.")
        logger.info("Pre-augmented data is available at T016c output.")
        return

    # If we are here, either n > 150 (subsampled) or n < 50 (all kept, but potentially subsampled logic applied)
    # According to T018, if n > 150 or n < 50, we subsample to 150 (or keep all if n < 50).
    # We expect the subsampled file to exist if T018 ran successfully.
    
    if not os.path.exists(str(subsampled_path)):
        # Fallback: Try to load the processed graph dataset directly if subsampling wasn't strictly needed or failed silently
        # But per T018 logic, if we are here, we should have a subsampled file or the logic implies we handle it.
        # Let's assume T018 produced the file. If not, we fail loudly.
        raise FileNotFoundError(
            f"Subsampled dataset not found at {subsampled_path}. "
            "T018 (Subsampling) must complete successfully before T019."
        )

    logger.info(f"Loading subsampled dataset from {subsampled_path}")
    df = load_processed_polyester_dataset(str(subsampled_path))

    logger.info(f"Saving final processed dataset to {final_output_path}")
    save_dataset(df, str(final_output_path), str(checksum_path))

    logger.info("T019 Data Saving completed successfully.")

if __name__ == "__main__":
    main()