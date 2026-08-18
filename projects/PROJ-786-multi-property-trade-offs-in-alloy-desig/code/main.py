"""
Orchestration script for the Alloy Design Pipeline.
Runs data ingestion and feature encoding, saving the final processed dataset.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data_ingestion import load_oqmd_data, filter_valid_entries, save_processed_data
from code.feature_encoder import encode_dataframe, save_encoded_data
from code.config import load_environment, get_config
from code.utils.logging_config import configure_root_logger, log_info_with_context, log_error_with_context

logger = logging.getLogger(__name__)

def run_ingestion_step(config: dict) -> bool:
    """
    Executes the data ingestion pipeline:
    1. Fetches OQMD data.
    2. Filters for valid Bulk/Shear Moduli entries.
    3. Saves the intermediate raw/filtered data.
    
    Returns True if successful and data is available for encoding.
    """
    log_info_with_context("Starting Data Ingestion Step", context="T015-Orchestration")
    
    try:
        # Load data from real source (OQMD via HuggingFace)
        # This function handles the 'load_dataset' call and fails loudly if source is unreachable
        raw_df = load_oqmd_data()
        
        if raw_df is None or raw_df.empty:
            log_error_with_context("Failed to load OQMD data. Exiting.", context="T015-Orchestration")
            return False

        log_info_with_context(f"Loaded {len(raw_df)} raw entries from OQMD.", context="T015-Orchestration")

        # Filter entries
        filtered_df = filter_valid_entries(raw_df)
        
        if filtered_df.empty:
            log_error_with_context("No valid entries found after filtering (Bulk/Shear > 0).", context="T015-Orchestration")
            return False

        log_info_with_context(f"Filtered data: {len(filtered_df)} valid entries remaining.", context="T015-Orchestration")

        # Save intermediate processed data
        output_path = Path(config.get("data_dir", "data")) / "processed" / "raw_filtered_alloys.csv"
        save_processed_data(filtered_df, str(output_path))
        
        log_info_with_context(f"Saved intermediate data to {output_path}", context="T015-Orchestration")
        return True

    except Exception as e:
        log_error_with_context(f"Error during ingestion: {str(e)}", context="T015-Orchestration")
        return False

def run_encoding_step(config: dict) -> bool:
    """
    Executes the feature encoding pipeline:
    1. Loads the filtered data from the ingestion step.
    2. Encodes compositions using elemental fractions and periodic descriptors.
    3. Saves the final encoded dataset.
    
    Returns True if successful.
    """
    log_info_with_context("Starting Feature Encoding Step", context="T015-Orchestration")
    
    input_path = Path(config.get("data_dir", "data")) / "processed" / "raw_filtered_alloys.csv"
    
    if not os.path.exists(input_path):
        log_error_with_context(f"Input file not found: {input_path}. Run ingestion first.", context="T015-Orchestration")
        return False

    try:
        # Load the filtered data
        # Re-using the internal logic or loading via pandas if needed. 
        # Assuming save_processed_data uses standard CSV format.
        import pandas as pd
        df = pd.read_csv(input_path)
        
        if df.empty:
            log_error_with_context("Input dataframe is empty.", context="T015-Orchestration")
            return False

        log_info_with_context(f"Loaded {len(df)} entries for encoding.", context="T015-Orchestration")

        # Encode compositions
        encoded_df = encode_dataframe(df)
        
        if encoded_df is None or encoded_df.empty:
            log_error_with_context("Encoding resulted in empty dataframe.", context="T015-Orchestration")
            return False

        # Save final output
        output_path = Path(config.get("data_dir", "data")) / "processed" / "encoded_alloys.csv"
        save_encoded_data(encoded_df, str(output_path))
        
        log_info_with_context(f"Successfully saved encoded data to {output_path}", context="T015-Orchestration")
        return True

    except Exception as e:
        log_error_with_context(f"Error during encoding: {str(e)}", context="T015-Orchestration")
        return False

def main():
    """
    Main entry point for the orchestration script.
    """
    parser = argparse.ArgumentParser(description="Orchestrate Alloy Design Pipeline (Ingestion + Encoding)")
    parser.add_argument("--data-dir", type=str, default="data", help="Base directory for data artifacts")
    parser.add_argument("--env-file", type=str, default=".env", help="Path to .env file")
    args = parser.parse_args()

    # Setup logging
    configure_root_logger(level=logging.INFO)
    
    # Load configuration
    load_environment(env_path=args.env_file)
    config = get_config()
    config["data_dir"] = args.data_dir

    start_time = datetime.now()
    log_info_with_context(f"Pipeline started at {start_time}", context="T015-Orchestration")

    success = True

    # Step 1: Ingestion
    if not run_ingestion_step(config):
        success = False
    
    if success:
        # Step 2: Encoding
        if not run_encoding_step(config):
            success = False

    end_time = datetime.now()
    duration = end_time - start_time

    if success:
        log_info_with_context(f"Pipeline completed successfully in {duration}", context="T015-Orchestration")
        sys.exit(0)
    else:
        log_error_with_context("Pipeline failed.", context="T015-Orchestration")
        sys.exit(1)

if __name__ == "__main__":
    main()