"""
Descriptor computation module.
Computes Magpie compositional descriptors and saves to data/processed/.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from magpie import Magpie
from magpie.utils import ElementProperty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Updated input path to match merged/preprocessed output from T006f/T007a
INPUT_FILE = PROCESSED_DIR / "preprocessed_data.parquet"
OUTPUT_FILE = PROCESSED_DIR / "descriptors.parquet"

def load_raw_data() -> pd.DataFrame:
    """Loads the preprocessed data from data/processed/preprocessed_data.parquet."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}. "
            "Ensure T007a (preprocessing) has completed successfully."
        )
    logger.info(f"Loading preprocessed data from {INPUT_FILE}")
    return pd.read_parquet(INPUT_FILE)

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Magpie compositional descriptors for each formula.
    Applies L2-normalization to the computed descriptors.
    Returns a DataFrame with formula, target properties, and normalized descriptors.
    """
    if 'formula' not in df.columns:
        raise ValueError("Input data must contain a 'formula' column.")

    logger.info("Computing Magpie descriptors...")
    
    # Initialize Magpie
    magpie = Magpie()
    
    formulas = df['formula'].tolist()
    
    # Compute descriptors
    descriptors_df = magpie.compute(formulas)
    
    # Ensure index matches original dataframe
    descriptors_df.index = df.index
    
    # Drop any rows with NaN (failed parsing)
    combined = pd.concat([df, descriptors_df], axis=1)
    combined = combined.dropna(subset=descriptors_df.columns)
    
    logger.info(f"Computed descriptors for {len(combined)} samples.")
    
    # Apply L2-normalization to descriptor columns only (not formula or targets)
    # Identify descriptor columns (exclude 'formula' and any target columns if known)
    # For safety, we assume non-string columns that are not 'formula' are descriptors
    # But more robustly, we can check against the original df columns
    original_cols = set(df.columns)
    descriptor_cols = [col for col in combined.columns if col not in original_cols]
    
    if not descriptor_cols:
        logger.warning("No descriptor columns found. Skipping normalization.")
        return combined
    
    logger.info(f"Applying L2-normalization to {len(descriptor_cols)} descriptor columns.")
    
    # L2-normalize each row (axis=1) for descriptor columns
    descriptor_matrix = combined[descriptor_cols].values
    norms = np.linalg.norm(descriptor_matrix, axis=1, keepdims=True)
    
    # Avoid division by zero
    norms = np.where(norms == 0, 1, norms)
    normalized_descriptors = descriptor_matrix / norms
    
    combined[descriptor_cols] = normalized_descriptors
    
    logger.info("L2-normalization complete.")
    return combined

def save_descriptors(df: pd.DataFrame):
    """Saves the computed descriptors to data/processed/descriptors.parquet."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_FILE, index=False)
    logger.info(f"Descriptors saved to {OUTPUT_FILE}")

def main():
    """Main entry point for descriptor computation."""
    logger.info("Starting descriptor computation...")
    df = load_raw_data()
    result = compute_descriptors(df)
    save_descriptors(result)
    logger.info("Descriptor computation completed.")

if __name__ == "__main__":
    main()
