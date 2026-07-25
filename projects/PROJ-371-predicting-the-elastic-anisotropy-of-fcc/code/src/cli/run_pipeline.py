"""
Orchestration script for the Elastic Anisotropy Data Pipeline.

This script fetches elastic constants, cleans the data, computes features,
and saves the final processed dataset.
"""
import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Import pipeline stages from sibling modules
from src.data.ingest import ingest_elastic_data
from src.data.clean import clean_elastic_data
from src.data.features import compute_compositional_features
from src.utils.config import get_config, get_path, ensure_directories, validate_api_keys
from src.utils.logging import setup_logger, get_logger

def validate_output_descriptors(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate that the output DataFrame has no null values in key descriptor columns.
    
    Args:
        df: The processed DataFrame.
        logger: The logger instance.
        
    Returns:
        True if validation passes, False otherwise.
    """
    required_columns = ['C11', 'C12', 'C44', 'A1']
    # Add compositional features that should be present
    compositional_cols = ['atomic_radius_variance', 'electronegativity_std', 'valence_electron_concentration']
    
    all_required = required_columns + compositional_cols
    
    missing_cols = [col for col in all_required if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in output: {missing_cols}")
        return False
    
    for col in all_required:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            logger.error(f"Column '{col}' contains {null_count} null values")
            return False
    
    logger.info("Output validation passed: All required columns present and non-null.")
    return True

def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the pipeline orchestration.
    
    Args:
        argv: Command line arguments (optional).
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(description="Run the Elastic Anisotropy Data Pipeline")
    parser.add_argument(
        "--validate", 
        action="store_true", 
        help="Validate output descriptors after pipeline execution"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to the manifest file (overrides config)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output CSV file (overrides config)"
    )
    
    args = parser.parse_args(argv)
    
    # Setup logging
    logger = setup_logger("pipeline", level=logging.INFO)
    
    logger.info("Starting Elastic Anisotropy Data Pipeline")
    
    try:
        # Load configuration
        config = get_config()
        
        # Validate API keys
        if not validate_api_keys(config):
            logger.error("API key validation failed. Check environment variables.")
            return 1
        
        # Ensure output directories exist
        ensure_directories(config)
        
        # Determine paths
        manifest_path = args.manifest or get_path(config, "raw_manifest")
        output_path = args.output or get_path(config, "processed_anisotropy")
        
        logger.info(f"Using manifest: {manifest_path}")
        logger.info(f"Output will be saved to: {output_path}")
        
        # Step 1: Ingest data
        logger.info("Step 1: Ingesting elastic constants...")
        raw_df = ingest_elastic_data(manifest_path, logger)
        
        if raw_df is None or raw_df.empty:
            logger.error("Ingestion failed or returned empty dataset.")
            return 1
        
        logger.info(f"Ingested {len(raw_df)} entries.")
        
        # Step 2: Clean data
        logger.info("Step 2: Cleaning data...")
        cleaned_df = clean_elastic_data(raw_df, logger)
        
        if cleaned_df is None or cleaned_df.empty:
            logger.error("Cleaning failed or resulted in empty dataset.")
            return 1
        
        logger.info(f"Cleaned dataset contains {len(cleaned_df)} entries.")
        
        # Step 3: Feature engineering
        logger.info("Step 3: Computing compositional features...")
        final_df = compute_compositional_features(cleaned_df, logger)
        
        if final_df is None or final_df.empty:
            logger.error("Feature engineering failed or resulted in empty dataset.")
            return 1
        
        logger.info(f"Final dataset contains {len(final_df)} entries with features.")
        
        # Step 4: Validate if requested
        if args.validate:
            logger.info("Step 4: Validating output descriptors...")
            if not validate_output_descriptors(final_df, logger):
                logger.error("Output validation failed.")
                return 1
        
        # Step 5: Save output
        logger.info("Step 4: Saving processed data...")
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_path, index=False)
        
        logger.info(f"Pipeline completed successfully. Output saved to {output_path}")
        return 0
        
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
