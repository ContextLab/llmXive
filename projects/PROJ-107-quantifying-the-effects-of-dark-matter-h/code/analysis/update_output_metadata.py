"""
Script to add associational_only=true flag to all output datasets.

This script should be run after the following tasks generate their output files:
- T017: data/processed/halo_shapes.csv
- T025: data/processed/statistical_results.csv
- T030: data/processed/sensitivity_report.csv
- T031-Analyze: data/processed/millennium_results.csv (if available)
- T038: data/processed/alignment_angles.csv

The script adds:
1. A column 'associational_only=true' to each CSV file
2. Updates data/metadata.yaml with the flag for each dataset
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import yaml

from utils.config import get_project_root, get_data_processed_path
from analysis.metadata_utils import (
    load_metadata,
    save_metadata,
    add_associational_only_flag_to_dataset,
    add_associational_only_flag_to_csv,
    flag_all_output_datasets
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for adding associational_only flag to all outputs."""
    logger.info("Starting associational_only flag update for all output datasets")
    
    # Get paths
    project_root = get_project_root()
    processed_path = get_data_processed_path()
    
    # Define output files
    output_files = [
        "halo_shapes.csv",
        "statistical_results.csv",
        "sensitivity_report.csv",
        "millennium_results.csv",
        "alignment_angles.csv"
    ]
    
    # Resolve full paths
    full_paths = [str(processed_path / f) for f in output_files]
    metadata_path = str(project_root / "data" / "metadata.yaml")
    
    # Filter to existing files
    existing_files = [f for f in full_paths if os.path.exists(f)]
    
    if not existing_files:
        logger.warning("No output files found to update. Ensure T017, T025, T030, T038 have run.")
        return
    
    logger.info(f"Found {len(existing_files)} output files to update")
    
    try:
        # Update all files
        metadata = flag_all_output_datasets(metadata_path, existing_files)
        
        logger.info("Successfully updated all output datasets with associational_only=true")
        logger.info(f"Updated metadata saved to: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Failed to update output datasets: {str(e)}")
        raise

if __name__ == "__main__":
    main()
