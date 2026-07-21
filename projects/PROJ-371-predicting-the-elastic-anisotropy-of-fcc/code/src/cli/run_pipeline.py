import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

# Import from project modules using the exact API surface provided
from src.utils.config import get_config, ensure_directories, get_path
from src.utils.logging import setup_logger, get_logger, log_info, log_error
from src.data.ingest import ingest_elastic_data
from src.data.clean import clean_elastic_data
from src.data.features import compute_compositional_features


def validate_output_descriptors(output_path: Path) -> bool:
    """
    Validate that the output CSV has no null values in descriptor columns.
    
    This implements US-1 Acceptance 2: Ensure output CSV has no null values
    in descriptor columns.
    
    Args:
        output_path: Path to the processed CSV file to validate
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        FileNotFoundError: If the output file does not exist
        ValueError: If null values are found in descriptor columns
    """
    logger = get_logger("pipeline_validation")
    
    if not output_path.exists():
        log_error(logger, f"Output file not found: {output_path}")
        raise FileNotFoundError(f"Output file not found: {output_path}")
    
    df = pd.read_csv(output_path)
    
    # Define the descriptor columns that must not have null values
    # These are the compositional features computed in features.py
    descriptor_columns = [
        'atomic_radius_variance',
        'electronegativity_std',
        'valence_electron_concentration'
    ]
    
    # Check if all expected columns exist
    missing_columns = [col for col in descriptor_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required descriptor columns: {missing_columns}"
        log_error(logger, error_msg)
        raise ValueError(error_msg)
    
    # Check for null values in descriptor columns
    null_counts = df[descriptor_columns].isnull().sum()
    total_nulls = null_counts.sum()
    
    if total_nulls > 0:
        error_details = []
        for col in descriptor_columns:
            if null_counts[col] > 0:
                error_details.append(f"{col}: {null_counts[col]} nulls")
        
        error_msg = f"Found {total_nulls} null values in descriptor columns: {'; '.join(error_details)}"
        log_error(logger, error_msg)
        raise ValueError(error_msg)
    
    log_info(logger, f"Validation passed: No null values in descriptor columns ({len(df)} rows)")
    return True


def main(args: Optional[list] = None) -> int:
    """
    Main pipeline orchestration script.
    
    Runs the full data pipeline: ingest, clean, feature engineering,
    and validation.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code: 0 for success, 1 for failure
    """
    parser = argparse.ArgumentParser(
        description="Run the elastic anisotropy prediction pipeline"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation on output descriptors after pipeline completion"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override default output path for processed data"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Setup logging
    logger = setup_logger("pipeline")
    log_info(logger, "Starting elastic anisotropy prediction pipeline")
    
    try:
        # Get configuration and ensure directories exist
        config = get_config()
        ensure_directories()
        
        # Define paths
        output_path = Path(parsed_args.output) if parsed_args.output else get_path("processed_elastic_data")
        
        # Step 1: Ingest data
        log_info(logger, "Step 1: Ingesting elastic constants data")
        raw_df = ingest_elastic_data()
        
        if raw_df is None or raw_df.empty:
            log_error(logger, "Ingest returned empty or None data")
            return 1
        
        log_info(logger, f"Ingested {len(raw_df)} entries")
        
        # Step 2: Clean data
        log_info(logger, "Step 2: Cleaning and filtering FCC data")
        clean_df = clean_elastic_data(raw_df)
        
        if clean_df is None or clean_df.empty:
            log_error(logger, "Clean returned empty or None data")
            return 1
        
        log_info(logger, f"Cleaned data: {len(clean_df)} entries")
        
        # Step 3: Compute features
        log_info(logger, "Step 3: Computing compositional features")
        feature_df = compute_compositional_features(clean_df)
        
        if feature_df is None or feature_df.empty:
            log_error(logger, "Feature engineering returned empty or None data")
            return 1
        
        log_info(logger, f"Feature engineering complete: {len(feature_df)} entries")
        
        # Step 4: Save output
        log_info(logger, f"Step 4: Saving processed data to {output_path}")
        feature_df.to_csv(output_path, index=False)
        log_info(logger, f"Saved {len(feature_df)} rows to {output_path}")
        
        # Step 5: Validate output if requested
        if parsed_args.validate:
            log_info(logger, "Step 5: Validating output descriptors")
            try:
                validate_output_descriptors(output_path)
                log_info(logger, "Validation successful")
            except (FileNotFoundError, ValueError) as e:
                log_error(logger, f"Validation failed: {str(e)}")
                return 1
        
        log_success(logger, "Pipeline completed successfully")
        return 0
        
    except Exception as e:
        log_error(logger, f"Pipeline failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    sys.exit(main())