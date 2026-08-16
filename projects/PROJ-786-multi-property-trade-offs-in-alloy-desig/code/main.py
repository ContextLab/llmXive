"""
Main orchestration script for the Alloy Design pipeline.
Executes the data ingestion and feature encoding steps sequentially.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import load_environment, parse_cli_args, get_config, verify_config
from data_ingestion import load_oqmd_data, filter_valid_entries, save_processed_data, main as ingestion_main
from feature_encoder import encode_dataframe, save_encoded_data, main as encoder_main
from utils.logging_config import configure_root_logger, log_info_with_context, log_error_with_context

def run_ingestion_step(config: dict) -> Path:
    """
    Executes the data ingestion pipeline:
    1. Loads raw OQMD data.
    2. Filters for valid Bulk/Shear modulus entries.
    3. Saves the filtered intermediate dataset.
    
    Returns the path to the filtered CSV.
    """
    log_info_with_context("Starting data ingestion step...", context="T015")
    
    # We call the main logic of data_ingestion directly but capture the output path
    # The ingestion module's main() typically prints to stdout, but we need the file path.
    # We will replicate the logic here to ensure we get the path and control flow.
    
    dataset_id = config.get('dataset_id', 'OQMD/elastic_properties')
    min_entries = config.get('min_entries', 500)
    output_dir = Path(config['paths']['processed'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    raw_path = output_dir / "oqmd_filtered_raw.csv"
    
    try:
        log_info_with_context(f"Loading dataset: {dataset_id}", context="T015")
        df_raw = load_oqmd_data(dataset_id)
        
        log_info_with_context(f"Loaded {len(df_raw)} raw entries", context="T015")
        
        log_info_with_context("Filtering for valid Bulk and Shear Moduli...", context="T015")
        df_valid = filter_valid_entries(df_raw)
        
        log_info_with_context(f"Filtered to {len(df_valid)} valid entries", context="T015")
        
        if len(df_valid) < min_entries:
            log_warning_with_context(
                f"Insufficient data for statistical analysis (N={len(df_valid)} < {min_entries}). "
                "Proceeding with available data but downstream analysis may be limited.",
                context="T015"
            )
            # Per T014, we do not exit with error, just log and continue
        
        log_info_with_context(f"Saving filtered data to {raw_path}", context="T015")
        save_processed_data(df_valid, raw_path)
        
        log_info_with_context("Ingestion step completed successfully.", context="T015")
        return raw_path
        
    except Exception as e:
        log_error_with_context(f"Failed during ingestion step: {str(e)}", context="T015")
        raise

def run_encoding_step(input_path: Path, config: dict) -> Path:
    """
    Executes the feature encoding pipeline:
    1. Loads the filtered CSV.
    2. Encodes compositions using elemental fractions and periodic descriptors.
    3. Saves the final encoded dataset.
    
    Returns the path to the encoded CSV.
    """
    log_info_with_context(f"Starting encoding step with input: {input_path}", context="T015")
    
    output_dir = Path(config['paths']['processed'])
    output_path = output_dir / "encoded_alloys.csv"
    
    try:
        # The feature_encoder module logic
        log_info_with_context("Loading filtered data for encoding...", context="T015")
        
        # We need to load the dataframe again to pass to the encoder
        import pandas as pd
        df_input = pd.read_csv(input_path)
        
        log_info_with_context("Encoding compositions and fetching periodic properties...", context="T015")
        df_encoded = encode_dataframe(df_input)
        
        log_info_with_context(f"Encoded {len(df_encoded)} entries. Feature dimensions: {df_encoded.shape[1]}", context="T015")
        
        log_info_with_context(f"Saving encoded data to {output_path}", context="T015")
        save_encoded_data(df_encoded, output_path)
        
        log_info_with_context("Encoding step completed successfully.", context="T015")
        return output_path
        
    except Exception as e:
        log_error_with_context(f"Failed during encoding step: {str(e)}", context="T015")
        raise

def main():
    """
    Main entry point for the orchestration script.
    Runs ingestion -> encoding -> versioning.
    """
    # Parse CLI args
    parser = argparse.ArgumentParser(description="Alloy Design Pipeline Orchestration")
    parser.add_argument('--dataset', type=str, default='OQMD/elastic_properties', help='HuggingFace dataset ID')
    parser.add_argument('--min-entries', type=int, default=500, help='Minimum entries required to proceed')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--variance-threshold', type=float, default=0.01, help='Variance threshold for feature selection')
    args = parser.parse_args()
    
    # Load environment and config
    load_environment()
    cli_config = {
        'dataset_id': args.dataset,
        'min_entries': args.min_entries,
        'seed': args.seed,
        'variance_threshold': args.variance_threshold,
        'paths': {
            'raw': 'data/raw',
            'processed': 'data/processed',
            'models': 'data/models',
            'results': 'data/results'
        }
    }
    
    # Verify config
    verify_config(cli_config)
    
    # Setup logging
    configure_root_logger(level=logging.INFO)
    
    start_time = datetime.now()
    log_info_with_context("Pipeline orchestration started.", context="T015")
    
    try:
        # Step 1: Ingestion
        filtered_path = run_ingestion_step(cli_config)
        
        if not filtered_path.exists():
            raise FileNotFoundError(f"Ingestion did not produce expected file: {filtered_path}")
        
        # Step 2: Encoding
        encoded_path = run_encoding_step(filtered_path, cli_config)
        
        if not encoded_path.exists():
            raise FileNotFoundError(f"Encoding did not produce expected file: {encoded_path}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_info_with_context(
            f"Pipeline completed successfully. Output: {encoded_path} (Duration: {duration:.2f}s)",
            context="T015"
        )
        
        # Optional: Run versioning on the output
        # from versioning import update_version_state
        # update_version_state(encoded_path, "encoded_alloys")
        
        return 0
        
    except Exception as e:
        log_error_with_context(f"Pipeline failed: {str(e)}", context="T015")
        return 1

if __name__ == "__main__":
    sys.exit(main())