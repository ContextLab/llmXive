"""
Pipeline script to execute data ingestion, preprocessing, and output generation.
This script orchestrates T009, T014b, T014c, T016, T017, T018, and T019.

It fetches real SLR data, cleans it, saves the CSV, computes the checksum,
and updates the project state file as per Constitution Principle III.
"""
import os
import sys
import json
import hashlib
import logging
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_config
from data.ingestion import validate_config, aggregate_satellites
from data.preprocessing import preprocess_slr_data
from data.output import compute_sha256, record_checksum, ensure_raw_data_preserved
from utils.logging import init_logging, get_logger, DataUnavailableError

def main():
    # Initialize logging
    init_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting SLR Data Ingestion and Preprocessing Pipeline (T019)")
    
    # 1. Load Config
    config = get_config()
    logger.info(f"Configuration loaded from {config.config_path}")
    
    # 2. Validate Data Availability (Gate from T009)
    # This ensures we don't proceed if verified_datasets.yaml is missing
    try:
        validate_config()
    except DataUnavailableError as e:
        logger.error(f"Data gate failed: {e}")
        sys.exit(1)
    
    # 3. Define Target Satellites
    # Based on project context: LAGEOS, Etalon, Starlette
    satellite_ids = ["LAGEOS-1", "LAGEOS-2", "ETALON-1", "ETALON-2", "STARLETTE"]
    logger.info(f"Target satellites: {satellite_ids}")
    
    # 4. Fetch and Aggregate Raw Data (T014c)
    # This calls the real fetch logic and parses the files
    try:
        raw_df = aggregate_satellites(satellite_ids)
    except Exception as e:
        logger.error(f"Failed to aggregate satellite data: {e}")
        sys.exit(1)
    
    if raw_df is None or raw_df.empty:
        logger.error("Aggregated data is empty. Cannot proceed.")
        sys.exit(1)
        
    logger.info(f"Aggregated {len(raw_df)} raw observations.")
    
    # 5. Preprocess Data (T016, T017, T018)
    # Filters residuals > 2cm, handles sparse data, aligns time series
    try:
        cleaned_df = preprocess_slr_data(raw_df)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)
        
    if cleaned_df is None or cleaned_df.empty:
        logger.error("Cleaned data is empty after filtering. Cannot proceed.")
        sys.exit(1)
        
    logger.info(f"Preprocessing complete. Remaining observations: {len(cleaned_df)}")
    
    # 6. Ensure Raw Data Preservation (T019 Requirement)
    # We assume the raw data is stored in data/raw/ by the ingestion step.
    # We verify the directory exists and is non-empty.
    raw_dir = Path(config.paths.raw_data_dir)
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist. Skipping preservation check.")
    else:
        ensure_raw_data_preserved(raw_dir)
        logger.info("Raw data preservation verified.")
    
    # 7. Save Cleaned Data to CSV (T019 Requirement)
    output_path = Path(config.paths.processed_data_dir) / "cleaned_slr_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cleaned_df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    
    # 8. Verify Output and Compute Checksum (T019 Requirement)
    if not output_path.exists() or output_path.stat().st_size == 0:
        logger.error(f"Output file {output_path} is missing or empty.")
        sys.exit(1)
        
    checksum = compute_sha256(output_path)
    logger.info(f"Checksum computed: {checksum}")
    
    # 9. Record Checksum in State File (T019 Requirement)
    # Path: state/projects/PROJ-752-testing-the-equivalence-principle-with-s.yaml
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "PROJ-752-testing-the-equivalence-principle-with-s.yaml"
    
    record_checksum(
        state_file=state_file,
        artifact_name="cleaned_slr_data.csv",
        checksum=checksum,
        path=str(output_path)
    )
    
    logger.info(f"Checksum recorded in {state_file}")
    logger.info("Pipeline T019 completed successfully.")
    
if __name__ == "__main__":
    main()
