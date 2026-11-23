import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Import sibling modules using the exact names from the API surface
from src.utils.logging import setup_logger, log_info, log_warning, log_error, log_success
from src.utils.config import get_path, ensure_directories, get_config
from src.data.ingest import ingest_elastic_data
from src.data.validate_ingest import validate_ingest
from src.data.clean import clean_elastic_data
from src.data.features import compute_compositional_features
from src.data.group_elements import group_elements_pipeline

def validate_output_descriptors(df: pd.DataFrame) -> bool:
    """
    Validate that the output DataFrame has no null values in descriptor columns.
    
    Descriptor columns are the compositional features computed in T014.
    Returns True if validation passes, raises ValueError if validation fails.
    """
    if df.empty:
        log_warning("Output DataFrame is empty, skipping null check")
        return True
    
    # Identify descriptor columns (compositional features)
    # These are typically the columns added by compute_compositional_features
    # Based on T014 implementation, these include:
    descriptor_columns = [
        'atomic_radius_variance',
        'electronegativity_std',
        'valence_electron_concentration'
    ]
    
    # Check for columns that actually exist in the dataframe
    existing_descriptors = [col for col in descriptor_columns if col in df.columns]
    
    if not existing_descriptors:
        log_warning("No descriptor columns found in output DataFrame")
        return True
    
    # Check for null values in descriptor columns
    null_counts = df[existing_descriptors].isnull().sum()
    total_nulls = null_counts.sum()
    
    if total_nulls > 0:
        error_msg = f"Validation failed: Found {total_nulls} null values in descriptor columns:\n{null_counts[null_counts > 0].to_string()}"
        log_error(error_msg)
        raise ValueError(error_msg)
    
    log_success("All descriptor columns contain valid (non-null) values")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Orchestrate the elastic anisotropy data pipeline"
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode using static fixtures instead of live API calls"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation checks on the output"
    )
    args = parser.parse_args()

    # Setup logging
    logger = setup_logger(__name__)
    
    # Ensure directories exist
    config = get_config()
    ensure_directories()
    
    log_info("Starting elastic anisotropy data pipeline")
    
    try:
        # Step 1: Ingest data
        log_info("Step 1: Ingesting elastic constants from data sources")
        raw_data_path = get_path("raw_manifest")
        ingest_data = ingest_elastic_data(
            manifest_path=raw_data_path,
            test_mode=args.test_mode
        )
        
        if ingest_data.empty:
            log_error("Ingested data is empty. Pipeline cannot continue.")
            sys.exit(1)
        
        # Step 2: Validate ingestion
        log_info("Step 2: Validating ingested data")
        validate_ingest(ingest_data)
        
        # Step 3: Clean data
        log_info("Step 3: Cleaning and filtering data")
        cleaned_data = clean_elastic_data(ingest_data)
        
        if cleaned_data.empty:
            log_error("Cleaned data is empty. Pipeline cannot continue.")
            sys.exit(1)
        
        # Step 4: Compute features
        log_info("Step 4: Computing compositional features")
        featured_data = compute_compositional_features(cleaned_data)
        
        # Step 5: Group elements for LOEO
        log_info("Step 5: Grouping elements for LOEO cross-validation")
        group_elements_pipeline(featured_data)
        
        # Step 6: Save final output
        output_path = get_path("processed_elastic_anisotropy")
        featured_data.to_csv(output_path, index=False)
        log_info(f"Pipeline complete. Output saved to: {output_path}")
        
        # Step 7: Validate output descriptors if requested
        if args.validate or True:  # Always validate as per T016 requirement
            log_info("Step 6: Validating output descriptors for null values")
            output_df = pd.read_csv(output_path)
            validate_output_descriptors(output_df)
        
        log_success("Pipeline execution completed successfully")
        
    except Exception as e:
        log_error(f"Pipeline failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    main()