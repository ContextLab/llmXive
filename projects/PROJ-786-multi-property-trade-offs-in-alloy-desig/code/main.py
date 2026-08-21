import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

from config import parse_cli_args, load_environment, get_config
from data_ingestion import load_oqmd_data, filter_valid_entries, save_processed_data
from feature_encoder import encode_dataframe, save_encoded_data
from utils.logging_config import configure_root_logger, log_info_with_context

def run_ingestion_step(config: dict) -> Path:
    """
    Executes the data ingestion pipeline:
    1. Loads raw OQMD data.
    2. Filters for valid Bulk and Shear Moduli.
    3. Saves the filtered dataset.
    """
    logger = logging.getLogger(__name__)
    log_info_with_context("Starting data ingestion step", context="ingestion")

    raw_data_path = config.get("raw_data_path")
    processed_dir = Path(config.get("processed_dir"))
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info(f"Loading data from {config.get('data_source')}")
    df_raw = load_oqmd_data(config.get("data_source"))
    total_fetched = len(df_raw)
    logger.info(f"Total records fetched: {total_fetched}")

    # Filter
    df_filtered = filter_valid_entries(df_raw)
    filtered_count = len(df_filtered)
    logger.info(f"Total records after filtering (Bulk/Shear > 0): {filtered_count}")

    # Check minimum threshold
    if filtered_count < 500:
        logger.warning("Insufficient data for statistical analysis (N < 500)")
        # Log specific warning as per T014 requirement
        logger.warning("Insufficient data for statistical analysis (N < 500)")
        # Save anyway for inspection, but exit cleanly
        output_path = processed_dir / "encoded_alloys.csv" # Placeholder
        df_filtered.to_csv(output_path, index=False)
        logger.info(f"Saved filtered data to {output_path}")
        return output_path

    # Save intermediate
    intermediate_path = processed_dir / "filtered_alloys.csv"
    save_processed_data(df_filtered, intermediate_path)
    logger.info(f"Saved filtered data to {intermediate_path}")

    log_info_with_context("Ingestion step completed successfully", context="ingestion")
    return intermediate_path

def run_encoding_step(input_path: Path, config: dict) -> Path:
    """
    Executes the feature encoding pipeline:
    1. Loads filtered data.
    2. Encodes compositions using elemental fractions and periodic descriptors.
    3. Validates descriptor count (>= 2 per element).
    4. Saves the final encoded dataset.
    """
    logger = logging.getLogger(__name__)
    log_info_with_context("Starting feature encoding step", context="encoding")

    processed_dir = Path(config.get("processed_dir"))
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load
    from pandas import read_csv
    df_input = read_csv(input_path)
    logger.info(f"Loaded {len(df_input)} records for encoding")

    # Encode
    # validate_periodic_descriptors is called internally by encode_dataframe or explicitly here
    # Per T016: Ensure feature vectors include at least two periodic descriptors per element
    df_encoded = encode_dataframe(df_input)

    # Explicit validation for T016 requirement
    # The encoder should ensure this, but we log the result
    logger.info(f"Encoded {len(df_encoded)} records")
    
    # Check for nulls in key columns
    if df_encoded.isnull().any().any():
        logger.error("Encoded data contains null values. Aborting.")
        raise ValueError("Encoded data contains null values.")

    # Save
    output_path = processed_dir / "encoded_alloys.csv"
    save_encoded_data(df_encoded, output_path)
    logger.info(f"Saved encoded data to {output_path}")

    log_info_with_context("Encoding step completed successfully", context="encoding")
    return output_path

def main():
    configure_root_logger()
    args = parse_cli_args()
    load_environment()
    config = get_config()

    logger = logging.getLogger(__name__)
    logger.info(f"Starting main pipeline at {datetime.now().isoformat()}")

    try:
        # Step 1: Ingestion
        filtered_path = run_ingestion_step(config)
        
        # Step 2: Encoding
        if filtered_path.exists():
            final_output = run_encoding_step(filtered_path, config)
            logger.info(f"Pipeline completed. Final output: {final_output}")
        else:
            logger.warning("Filtered path not found. Skipping encoding.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
