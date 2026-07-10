"""
Real Data Ingestion Module for Transient-Absorption Data.

This module implements the primary data source ingestion for the research pipeline.
It strictly enforces the presence of real experimental data files and fails
loudly if the required data is missing, preventing the pipeline from proceeding
with synthetic or placeholder data.

Output:
    Writes validated transient-absorption data to `data/processed/raw_traces.csv`.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional

import pandas as pd

# Project-relative imports based on provided API surface
# Adding code/ to path to ensure relative imports work when run as a script
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import setup_logging, log_environmental_params
from config import get_raw_data_path, get_processed_data_path

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Define the expected real data file name
REAL_DATA_FILENAME = "real_traces.csv"

def ingest_real_transient_absorption_data(
    input_filename: Optional[str] = None,
    output_filename: Optional[str] = None
) -> pd.DataFrame:
    """
    Ingests real transient-absorption data from a user-provided file path.

    This function is the primary entry point for real research data. It enforces
    a strict constraint: if the real data file is missing, the pipeline MUST fail
    with a clear, actionable error. No synthetic data is generated or used here.

    Args:
        input_filename: Optional override for the input filename. Defaults to
                        'real_traces.csv' located in the `data/raw/` directory.
        output_filename: Optional override for the output filename. Defaults to
                         'raw_traces.csv' located in the `data/processed/` directory.

    Returns:
        pd.DataFrame: The validated and loaded transient-absorption data.

    Raises:
        FileNotFoundError: If the specified real data file does not exist.
        ValueError: If the data file is empty or lacks required columns.
        RuntimeError: If the file format is invalid or cannot be parsed.
    """
    # Determine file paths using project config
    raw_data_dir = get_raw_data_path()
    processed_data_dir = get_processed_data_path()

    # Ensure directories exist
    os.makedirs(raw_data_dir, exist_ok=True)
    os.makedirs(processed_data_dir, exist_ok=True)

    # Resolve input path
    if input_filename is None:
        input_filename = REAL_DATA_FILENAME
    
    input_path = os.path.join(raw_data_dir, input_filename)

    # Resolve output path
    if output_filename is None:
        output_filename = "raw_traces.csv"
    
    output_path = os.path.join(processed_data_dir, output_filename)

    # --- CRITICAL CHECK: REAL DATA PRESENCE ---
    if not os.path.exists(input_path):
        error_msg = (
            f"CRITICAL ERROR: Real data file not found at '{input_path}'.\n"
            f"The pipeline requires real experimental data to proceed.\n"
            f"Please provide the file '{input_filename}' in the '{raw_data_dir}' directory.\n"
            f"This step cannot be bypassed with synthetic data for research purposes."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    logger.info(f"Found real data file at: {input_path}")

    # Load and validate data
    try:
        # Attempt to load CSV. Expecting columns: 'time_ns', 'absorbance', 'wavelength_nm', 'solvent'
        # Adjust dtype for time to handle scientific notation if present
        df = pd.read_csv(input_path)
    except Exception as e:
        error_msg = f"Failed to parse data file '{input_path}'. Ensure it is a valid CSV. Error: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    if df.empty:
        error_msg = f"Data file '{input_path}' is empty. Real data is required."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Validate required columns (basic schema check)
    # We expect at least time and absorbance for kinetic analysis
    required_columns = ['time_ns', 'absorbance']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        error_msg = (
            f"Data validation failed. Missing required columns: {missing_cols}. "
            f"Expected columns include: {required_columns}."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Log ingestion event with environmental context (using existing API)
    # We log that ingestion occurred; specific environmental params are logged by T014
    log_environmental_params("ingestion_start", {"status": "success", "file": input_filename})
    
    logger.info(f"Successfully ingested {len(df)} rows from real data.")
    logger.info(f"Data range: time_ns [{df['time_ns'].min():.4f} - {df['time_ns'].max():.4f}]")

    # Write to processed data directory for downstream tasks
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data written to: {output_path}")

    return df

def main():
    """
    CLI entry point for T015b: Real Data Ingestion.
    Runs the ingestion pipeline and exits with appropriate codes.
    """
    # Setup logging
    setup_logging()
    logger.info("Starting Real Data Ingestion (T015b)...")

    try:
        # Perform ingestion
        df = ingest_real_transient_absorption_data()
        
        logger.info("Ingestion completed successfully.")
        logger.info(f"Output saved to: {os.path.join(get_processed_data_path(), 'raw_traces.csv')}")
        
        # Return success
        return 0

    except FileNotFoundError as e:
        # Fail loudly as per task constraint
        print(f"\n{str(e)}\n", file=sys.stderr)
        return 1
    except (ValueError, RuntimeError) as e:
        print(f"\nData Error: {str(e)}\n", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"\nUnexpected Error during ingestion: {e}\n", file=sys.stderr)
        logger.exception("Unexpected error")
        return 3

if __name__ == "__main__":
    sys.exit(main())
