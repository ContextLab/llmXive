"""
Feature Engineering Pipeline Module.
Computes descriptors and saves to data/processed/alloys_features.csv.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

from src.features.descriptor_calculator import calculate_all_descriptors
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """Load preprocessed data."""
    input_path = Path("data/processed/alloys_raw.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {input_path}. Run preprocessing first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def apply_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Apply descriptor calculation to each row."""
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame with descriptor columns.")
        # Return empty DF with correct columns to avoid downstream errors
        descriptor_cols = [
            "average_electronegativity", "valence_electron_concentration",
            "atomic_radii_variance", "average_d_electrons", "atomic_size_mismatch"
        ]
        return df.assign(**{col: [] for col in descriptor_cols})
    
    logger.info("Calculating descriptors...")
    # Apply descriptor calculator
    # Assuming calculate_all_descriptors returns a dict of new columns
    # We map it to the dataframe
    
    # Simplified application for pipeline
    new_cols = calculate_all_descriptors(df)
    for col, val in new_cols.items():
        df[col] = val
        
    return df

def save_features(df: pd.DataFrame, output_path: Path):
    """Save features to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved features to {output_path} ({len(df)} rows).")

def run_feature_engineering_pipeline() -> pd.DataFrame:
    """Execute the feature engineering pipeline."""
    df = load_processed_data()
    if df.empty:
        logger.warning("Input data is empty. Saving empty features file.")
        save_features(df, Path("data/processed/alloys_features.csv"))
        return df
    
    df = apply_descriptors(df)
    save_features(df, Path("data/processed/alloys_features.csv"))
    return df

def main():
    """Entry point for feature engineering."""
    setup_logging("feature_engineering_pipeline", level=logging.INFO)
    df = run_feature_engineering_pipeline()
    return df

if __name__ == "__main__":
    main()
