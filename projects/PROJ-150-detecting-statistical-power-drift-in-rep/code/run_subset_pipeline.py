import os
import sys
import time
import json
import logging
import shutil
from pathlib import Path
import pandas as pd

# Import main pipeline logic
from main import run_pipeline

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
RESULTS_DIR = PROJECT_ROOT / "results"
LOG_DIR = PROJECT_ROOT / "logs"

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = LOG_DIR / "subset_run.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def create_subset_data(logger):
    """
    Creates a small static subset of the data for quick verification.
    If the full data exists, it samples a small number of rows.
    If not, it expects the download step to handle fetching.
    This function ensures a small, manageable dataset exists for T034 verification.
    """
    # Check if raw data exists
    raw_files = list(DATA_RAW_DIR.glob("*.csv"))
    if not raw_files:
        logger.warning("No raw data found. Skipping subset creation. Pipeline will attempt download.")
        return

    source_file = raw_files[0]
    logger.info(f"Found source file: {source_file}")

    # Read data
    try:
        df = pd.read_csv(source_file)
    except Exception as e:
        logger.error(f"Failed to read source file: {e}")
        return

    # Create a small subset (e.g., first 100 rows or 5% if larger)
    subset_size = min(100, len(df))
    subset_df = df.head(subset_size)
    
    subset_path = DATA_RAW_DIR / "subset_data.csv"
    subset_df.to_csv(subset_path, index=False)
    logger.info(f"Created subset data at {subset_path} with {len(subset_df)} rows.")

def run_pipeline_subset(logger):
    """
    Runs the pipeline. For T034, we assume the pipeline logic in main.py
    is robust enough to handle the data present in data/raw.
    We rely on the subset created above if available, or the full download.
    """
    logger.info("Starting subset pipeline execution...")
    
    # The main pipeline orchestrator (main.py) will handle the flow.
    # We assume it checks for data availability.
    try:
        run_pipeline()
        logger.info("Pipeline execution completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise

def main():
    logger = setup_logging()
    
    # Ensure directories
    (PROJECT_ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "derived").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)
    
    # Optionally create a subset if full data exists, 
    # but for T034 verification, we just need the pipeline to run end-to-end.
    # We call the main pipeline directly.
    run_pipeline_subset(logger)

if __name__ == "__main__":
    main()
