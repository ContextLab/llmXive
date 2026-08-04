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

INPUT_FILE = RAW_DIR / "raw_oqmd_constitution.csv"
OUTPUT_FILE = PROCESSED_DIR / "descriptors.csv"

def load_raw_data() -> pd.DataFrame:
    """Loads the raw constitution data."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Raw data file not found: {INPUT_FILE}. Run code/ingestion.py first.")
    return pd.read_csv(INPUT_FILE)

def compute_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Magpie descriptors for each formula.
    Returns a DataFrame with formula and descriptor columns.
    """
    if 'formula' not in df.columns:
        raise ValueError("Input data must contain a 'formula' column.")

    logger.info("Computing Magpie descriptors...")
    
    # Initialize Magpie with standard settings
    # Magpie typically computes 14 descriptors by default (mean, min, max, range, std, etc. for 7 properties)
    # We use the default configuration which returns 14 features per property set, but usually 
    # the standard Magpie implementation returns a fixed set of 14 compositional descriptors.
    
    magpie = Magpie()
    
    # Compute descriptors
    # The magpie library expects a list of formulas
    formulas = df['formula'].tolist()
    
    # Magpie.compute returns a DataFrame with descriptors
    descriptors_df = magpie.compute(formulas)
    
    # Ensure index matches original dataframe
    descriptors_df.index = df.index
    
    # Merge with original data (formula, etc.)
    result = pd.concat([df, descriptors_df], axis=1)
    
    # Drop NaN rows if any (e.g., formulas that couldn't be parsed)
    result = result.dropna()
    
    logger.info(f"Computed descriptors for {len(result)} samples.")
    return result

def save_descriptors(df: pd.DataFrame):
    """Saves the computed descriptors to CSV."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
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
