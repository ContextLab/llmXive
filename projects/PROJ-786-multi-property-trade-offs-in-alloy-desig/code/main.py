"""
Main orchestration script for the Multi-Property Trade-Offs in Alloy Design pipeline.

This script orchestrates the data ingestion and feature encoding steps,
ensuring the full pipeline runs end-to-end and saves the final processed dataset.

Usage:
    python code/main.py [--variance_threshold FLOAT] [--seed INT]

Output:
    data/processed/encoded_alloys.csv
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path to ensure imports work correctly
# Assuming this script is run from the project root or code directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_environment, parse_cli_args, get_config, verify_config
from data_ingestion import load_oqmd_data, filter_valid_entries, save_processed_data
from feature_encoder import encode_dataframe, save_encoded_data
from utils.logging_config import configure_root_logger, log_info_with_context, log_error_with_context
from versioning import update_version_state


def run_ingestion_step(config: dict) -> tuple:
    """
    Execute the data ingestion pipeline.

    Args:
        config: Configuration dictionary containing paths and parameters.

    Returns:
        tuple: (raw_df, filtered_df)
    """
    log_info_with_context("Starting data ingestion step.")
    
    try:
        # Load raw data from OQMD via HuggingFace
        log_info_with_context("Fetching OQMD data from HuggingFace...")
        raw_df = load_oqmd_data()
        
        if raw_df is None or raw_df.empty:
            log_error_with_context("Failed to load OQMD data. Exiting.")
            return None, None

        log_info_with_context(f"Loaded {len(raw_df)} raw entries.")

        # Filter valid entries (Bulk and Shear Moduli > 0)
        log_info_with_context("Filtering entries for valid Bulk and Shear Moduli...")
        filtered_df = filter_valid_entries(raw_df)
        
        if filtered_df is None or filtered_df.empty:
            log_info_with_context("Insufficient data for statistical analysis (N < 500) after filtering. Exiting gracefully.")
            return None, None

        log_info_with_context(f"Filtered dataset contains {len(filtered_df)} valid entries.")

        # Save intermediate processed data (optional, for debugging)
        processed_path = Path(config['paths']['data_processed']) / "intermediate_filtered.csv"
        save_processed_data(filtered_df, str(processed_path))
        log_info_with_context(f"Saved intermediate filtered data to {processed_path}")

        return raw_df, filtered_df

    except Exception as e:
        log_error_with_context(f"Error during ingestion step: {str(e)}")
        return None, None


def run_encoding_step(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Execute the feature encoding pipeline.

    Args:
        df: Filtered DataFrame with valid alloy entries.
        config: Configuration dictionary.

    Returns:
        pd.DataFrame: Encoded DataFrame with feature vectors.
    """
    log_info_with_context("Starting feature encoding step.")
    
    try:
        # Encode compositions using elemental fractions and periodic descriptors
        encoded_df = encode_dataframe(df, config)
        
        if encoded_df is None or encoded_df.empty:
            log_error_with_context("Encoding failed. Exiting.")
            return None

        log_info_with_context(f"Encoded dataset shape: {encoded_df.shape}")
        
        # Validate no nulls in key columns
        key_cols = ['bulk_modulus', 'shear_modulus']
        # Assuming encoded columns start with 'feature_' or similar, but checking target cols is critical
        null_counts = encoded_df[key_cols].isnull().sum()
        if null_counts.sum() > 0:
            log_error_with_context(f"Null values found in key columns after encoding: {null_counts.to_dict()}")
            return None

        return encoded_df

    except Exception as e:
        log_error_with_context(f"Error during encoding step: {str(e)}")
        return None


def main():
    """Main entry point for the orchestration script."""
    # Configure logging
    configure_root_logger(level=logging.INFO)
    
    log_info_with_context("Starting main orchestration pipeline.")

    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Orchestrate Alloy Design Pipeline")
    parser.add_argument('--variance_threshold', type=float, default=0.01, help='Variance threshold for feature selection')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()

    # Load environment and configuration
    load_environment()
    config = parse_cli_args(args)
    verify_config(config)

    # Ensure output directories exist
    Path(config['paths']['data_processed']).mkdir(parents=True, exist_ok=True)
    Path(config['paths']['data_raw']).mkdir(parents=True, exist_ok=True)

    # Step 1: Ingestion
    raw_df, filtered_df = run_ingestion_step(config)
    
    if filtered_df is None:
        log_info_with_context("Pipeline halted due to insufficient valid data.")
        # T014 requirement: Exit with code 0 if N < 500
        sys.exit(0)

    # Step 2: Encoding
    encoded_df = run_encoding_step(filtered_df, config)

    if encoded_df is None:
        log_error_with_context("Pipeline failed during encoding.")
        sys.exit(1)

    # Step 3: Save Final Output
    output_path = Path(config['paths']['data_processed']) / "encoded_alloys.csv"
    try:
        save_encoded_data(encoded_df, str(output_path))
        log_info_with_context(f"Successfully saved final encoded dataset to {output_path}")
    except Exception as e:
        log_error_with_context(f"Failed to save final output: {str(e)}")
        sys.exit(1)

    # Step 4: Update Versioning State
    try:
        update_version_state(config, output_path)
        log_info_with_context("Version state updated successfully.")
    except Exception as e:
        log_error_with_context(f"Failed to update version state: {str(e)}")
        # Non-fatal, but log it

    log_info_with_context("Pipeline completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    # Ensure pandas is available for type hints in the function signature above
    import pandas as pd
    main()
