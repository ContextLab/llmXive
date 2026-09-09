"""
Generate alignment angles dataset for User Story 4.

This script computes misalignment angles (spin-spin, major-major) for halo-galaxy
pairs and outputs the results to data/processed/alignment_angles.csv.
It also applies the associational_only=true flag as required by T026.

Dependencies:
- data/processed/halo_shapes.csv (from T017)
- data/raw/tng/snapshot_000/ (TNG-100 data files)

Output:
- data/processed/alignment_angles.csv
"""
import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_data_processed_path, get_data_raw_path
from utils.logging import get_pipeline_logger
from processing.alignment import align_halo_galaxy_pairs
from analysis.metadata_utils import add_associational_only_flag_to_csv

# Configure logging
logger = get_pipeline_logger(__name__)

def load_halo_shapes() -> pd.DataFrame:
    """Load the processed halo shapes data."""
    halo_shapes_path = get_data_processed_path() / "halo_shapes.csv"
    if not halo_shapes_path.exists():
        raise FileNotFoundError(f"Required input file not found: {halo_shapes_path}")
    
    logger.info(f"Loading halo shapes from {halo_shapes_path}")
    df = pd.read_csv(halo_shapes_path)
    logger.info(f"Loaded {len(df)} halo records")
    return df

def load_galaxy_properties() -> pd.DataFrame:
    """
    Load galaxy properties from TNG-100 data.
    Since we don't have a specific loader for galaxy properties yet,
    we'll extract them from the TNG halo data or use a placeholder approach
    that fails loudly if real data isn't available.
    """
    # For this implementation, we assume galaxy properties are embedded in
    # the TNG halo data or available via the same loader mechanism.
    # In a real scenario, this would call a specific galaxy property loader.
    
    # Check if TNG data exists
    tng_data_path = get_data_raw_path() / "tng" / "snapshot_000"
    if not tng_data_path.exists():
        raise FileNotFoundError(
            f"TNG-100 data directory not found: {tng_data_path}. "
            "Please run the TNG data ingestion pipeline first."
        )
    
    logger.info(f"Loading galaxy properties from {tng_data_path}")
    
    # In a real implementation, we would load galaxy properties from the
    # TNG data files. For now, we'll simulate this with a placeholder that
    # fails loudly if the data isn't available.
    # This is a simplified version - in practice, we'd load from HDF5 files.
    
    # Attempt to load from a pre-processed galaxy properties file if it exists
    galaxy_props_path = get_data_processed_path() / "galaxy_properties.csv"
    if galaxy_props_path.exists():
        logger.info(f"Loading pre-processed galaxy properties from {galaxy_props_path}")
        return pd.read_csv(galaxy_props_path)
    
    # If no pre-processed file exists, we need to extract from raw TNG data
    # This is a simplified approach - in reality, we'd parse the HDF5 files
    logger.warning("No pre-processed galaxy properties found. Attempting to extract from raw TNG data.")
    
    # For this implementation, we'll create a minimal placeholder that fails loudly
    # if the real data extraction isn't implemented. This ensures we don't
    # fabricate data.
    raise NotImplementedError(
        "Galaxy property extraction from raw TNG data not yet implemented. "
        "Please implement the galaxy property loader in code/ingestion/galaxy_loader.py "
        "or provide a pre-processed galaxy_properties.csv file."
    )

def compute_alignment_angles(halo_df: pd.DataFrame, galaxy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute misalignment angles for halo-galaxy pairs.
    
    Args:
        halo_df: DataFrame with halo shape metrics
        galaxy_df: DataFrame with galaxy properties and position data
        
    Returns:
        DataFrame with alignment angles and related metrics
    """
    logger.info(f"Computing alignment angles for {len(halo_df)} haloes")
    
    # Use the alignment processing function from the alignment module
    alignment_results = align_halo_galaxy_pairs(halo_df, galaxy_df)
    
    logger.info(f"Computed alignment angles for {len(alignment_results)} pairs")
    return alignment_results

def save_alignment_results(results_df: pd.DataFrame, output_path: Path) -> None:
    """Save alignment results to CSV."""
    logger.info(f"Saving alignment results to {output_path}")
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(results_df)} records to {output_path}")

def apply_associational_flag(output_path: Path) -> None:
    """Apply the associational_only=true flag to the output CSV."""
    logger.info(f"Applying associational_only flag to {output_path}")
    add_associational_only_flag_to_csv(output_path)
    logger.info("Successfully applied associational_only flag")

def main():
    """Main entry point for the alignment report generation."""
    try:
        # Ensure output directory exists
        output_dir = get_data_processed_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define output path
        output_path = output_dir / "alignment_angles.csv"
        
        logger.info("Starting alignment angles generation")
        
        # Load input data
        halo_df = load_halo_shapes()
        
        # For this implementation, we'll create a minimal galaxy properties
        # DataFrame with the required fields if the real loader isn't available.
        # This is a temporary workaround that will be replaced with real data loading.
        # IMPORTANT: This is a placeholder that fails loudly if real data isn't available.
        try:
            galaxy_df = load_galaxy_properties()
        except NotImplementedError as e:
            logger.error(str(e))
            logger.error("Cannot proceed without real galaxy property data.")
            logger.error("Please implement the galaxy property loader or provide pre-processed data.")
            raise
        
        # Compute alignment angles
        alignment_results = compute_alignment_angles(halo_df, galaxy_df)
        
        # Save results
        save_alignment_results(alignment_results, output_path)
        
        # Apply associational flag
        apply_associational_flag(output_path)
        
        logger.info("Alignment angles generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during alignment angles generation: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
