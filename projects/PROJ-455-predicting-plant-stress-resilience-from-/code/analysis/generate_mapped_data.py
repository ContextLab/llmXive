"""
Script to generate the mapped_data.parquet artifact required by T026.
This script generates synthetic data, maps it to KEGG, and saves the result.
"""
import os
import sys
import pandas as pd
import numpy as np
from data.generator import generate_synthetic_data
from analysis.pathway import map_to_kegg
from utils.logging import get_logger

logger = get_logger(__name__)

def main():
    """
    Main entry point to generate mapped data.
    """
    logger.info("Starting mapped data generation...")
    
    # Generate synthetic data if not present
    synthetic_path = "data/raw/synthetic_drought_42.parquet"
    if not os.path.exists(synthetic_path):
        logger.info(f"Generating synthetic data at {synthetic_path}")
        generate_synthetic_data(
            n_samples=200,
            stress_type="drought",
            missing_rate=0.05,
            seed=42
        )
    
    # Load the synthetic data
    logger.info(f"Loading synthetic data from {synthetic_path}")
    df = pd.read_parquet(synthetic_path)
    
    # Map to KEGG (this will save mapped_data.parquet)
    logger.info("Mapping metabolites to KEGG IDs...")
    mapped_df = map_to_kegg(df)
    
    logger.info(f"Successfully generated mapped data with {len(mapped_df)} rows.")
    logger.info("Mapped data generation complete.")
    return mapped_df

if __name__ == "__main__":
    main()
