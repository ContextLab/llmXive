import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

from utils import setup_logging, get_logger

logger = get_logger(__name__)

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"

def main():
    """
    Combine cleaned.csv and split_indices.json into train_val_test.csv.
    """
    setup_logging()
    logger.info("Starting merge split pipeline...")

    cleaned_path = PROCESSED_DIR / "cleaned.csv"
    indices_path = PROCESSED_DIR / "split_indices.json"
    output_path = PROCESSED_DIR / "train_val_test.csv"

    if not cleaned_path.exists():
        logger.error(f"Cleaned data not found: {cleaned_path}")
        sys.exit(1)

    if not indices_path.exists():
        logger.error(f"Split indices not found: {indices_path}")
        sys.exit(1)

    # Load data
    df = pd.read_csv(cleaned_path)
    with open(indices_path, 'r') as f:
        split_indices = json.load(f)

    # Create a mapping from smi to split
    smi_to_split = {}
    for split_name, smiles_list in split_indices.items():
        for smi in smiles_list:
            smi_to_split[smi] = split_name

    # Assign split column
    # Ensure we only keep rows that are in the split indices (sanity check)
    # and handle any rows in cleaned.csv that might have been dropped or not in indices
    df['split'] = df['smi'].map(smi_to_split)
    
    # Filter out any rows that didn't make it into the split (should be none if logic is correct)
    df = df.dropna(subset=['split'])

    # Sort by smi
    df = df.sort_values('smi').reset_index(drop=True)

    # Save
    df.to_csv(output_path, index=False)
    logger.info(f"Merged data saved to {output_path} with {len(df)} rows.")

    logger.info("Merge split pipeline completed successfully.")

if __name__ == "__main__":
    main()