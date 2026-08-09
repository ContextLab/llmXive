"""
Script to generate statistical results CSV (T025).

This script performs the full statistical analysis pipeline on the processed
halo shapes data and galaxy properties, generating a comprehensive CSV
file with correlation coefficients, p-values, and regression results.

Output: data/processed/statistical_results.csv
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_data_processed_path, get_project_root, load_config
from utils.logging import get_pipeline_logger, log_metric, log_error
from analysis.run_statistical_analysis import (
    load_halo_data,
    load_galaxy_properties,
    merge_halo_galaxy_data,
    run_statistical_tests,
    apply_bonferroni_correction
)
from analysis.stats import apply_bonferroni_correction as bonferroni_func

# Configure logger
logger = get_pipeline_logger(__name__)

def load_metadata() -> Dict[str, Any]:
    """Load project metadata."""
    metadata_path = get_project_root() / "data" / "metadata.yaml"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_metadata(metadata: Dict[str, Any]) -> None:
    """Save updated metadata."""
    metadata_path = get_project_root() / "data" / "metadata.yaml"
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def add_associational_only_flag(df: pd.DataFrame) -> pd.DataFrame:
    """Add associational_only=true flag to dataframe."""
    df['associational_only'] = True
    return df

def main():
    """Main entry point for generating statistical results."""
    logger.info("Starting statistical results generation (T025)")
    
    try:
        # Load configuration
        config = load_config()
        processed_path = get_data_processed_path()
        
        # Ensure output directory exists
        processed_path.mkdir(parents=True, exist_ok=True)
        
        # Load input data
        logger.info("Loading halo shape data...")
        halo_df = load_halo_data()
        if halo_df is None or halo_df.empty:
            logger.error("No halo data found. Cannot proceed with analysis.")
            log_error("No halo data found for statistical analysis")
            return
        
        logger.info(f"Loaded {len(halo_df)} halo records")
        
        # Load galaxy properties
        logger.info("Loading galaxy properties...")
        galaxy_df = load_galaxy_properties()
        if galaxy_df is None or galaxy_df.empty:
            logger.error("No galaxy property data found. Cannot proceed with analysis.")
            log_error("No galaxy property data found for statistical analysis")
            return
        
        logger.info(f"Loaded {len(galaxy_df)} galaxy records")
        
        # Merge datasets
        logger.info("Merging halo and galaxy data...")
        merged_df = merge_halo_galaxy_data(halo_df, galaxy_df)
        if merged_df is None or merged_df.empty:
            logger.error("Merged dataset is empty. Check join keys.")
            log_error("Merged dataset empty after joining halo and galaxy data")
            return
        
        logger.info(f"Merged dataset contains {len(merged_df)} records")
        
        # Run statistical tests
        logger.info("Running statistical tests...")
        results = run_statistical_tests(merged_df)
        
        if not results:
            logger.warning("No statistical results generated.")
            log_error("Statistical tests returned no results")
            return
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Apply Bonferroni correction
        logger.info("Applying Bonferroni correction...")
        corrected_results = apply_bonferroni_correction(results_df)
        
        # Add metadata columns
        corrected_results['analysis_timestamp'] = datetime.now().isoformat()
        corrected_results['dataset_version'] = "1.0"
        
        # Add associational_only flag
        corrected_results = add_associational_only_flag(corrected_results)
        
        # Save to CSV
        output_path = processed_path / "statistical_results.csv"
        logger.info(f"Saving results to {output_path}")
        corrected_results.to_csv(output_path, index=False)
        
        # Log success metrics
        log_metric("statistical_results_rows", len(corrected_results))
        log_metric("statistical_tests_run", len(results))
        
        # Update metadata
        metadata = load_metadata()
        if 'outputs' not in metadata:
            metadata['outputs'] = {}
        metadata['outputs']['statistical_results'] = {
            'path': str(output_path.relative_to(project_root)),
            'rows': len(corrected_results),
            'tests': len(results),
            'bonferroni_corrected': True,
            'timestamp': datetime.now().isoformat()
        }
        save_metadata(metadata)
        
        logger.info("Statistical results generation completed successfully")
        return corrected_results
        
    except Exception as e:
        logger.error(f"Error during statistical results generation: {str(e)}")
        log_error(f"Statistical analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
