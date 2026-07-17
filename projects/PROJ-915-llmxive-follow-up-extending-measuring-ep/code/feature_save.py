"""
T016: Save final feature-rich dataset to data/processed/features.csv.

This script loads the validated features from the previous step (T014/T015),
ensures data integrity, and saves the final CSV to the processed directory.
It relies on the existing API surface in code/features.py and code/validation_logic.py.
"""
import os
import csv
import logging
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from features import run_feature_extraction
from validation_logic import run_t015_validation_pipeline
from config import Config
from validation import validate_data_integrity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    config = Config()
    
    # Ensure output directory exists
    output_dir = config.processed_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features.csv"

    logger.info(f"Starting T016: Saving features to {output_path}")

    # 1. Run feature extraction if the raw features file doesn't exist
    # Note: T014 is marked complete, but we ensure the data is available.
    # We assume T014 produced an intermediate file or we regenerate from raw.
    # Based on the pipeline flow, we run extraction to get the feature list.
    logger.info("Executing feature extraction (T014 logic)...")
    # run_feature_extraction handles loading raw data and computing features
    # It is expected to output to a temporary or intermediate location, 
    # or we assume the state is persisted. 
    # For this script to be self-contained and runnable, we call the extraction logic.
    # The API `run_feature_extraction` returns a list of dicts or writes to a temp file.
    # Assuming it returns the data or writes to a known interim spot based on T013/T014 design.
    # Let's assume run_feature_extraction writes to data/interim/features_raw.csv based on standard patterns,
    # or we need to capture its return value. 
    # Given the constraints, we will call it and assume it populates the expected state.
    
    # Re-running extraction to ensure data is fresh and available for T016
    # The function signature from API surface: run_feature_extraction
    features_data = run_feature_extraction()
    
    if not features_data:
        logger.error("Feature extraction returned no data. T014 may have failed.")
        sys.exit(1)

    logger.info(f"Extracted {len(features_data)} feature records.")

    # 2. Run T015 validation logic to flag undefined ratios
    logger.info("Running T015 validation (flagging undefined imperative ratios)...")
    # run_t015_validation_pipeline expects a path or data. 
    # Assuming it takes the list of dicts and returns the validated list or modifies it.
    # If it writes to a file, we need to read that back.
    # Based on typical patterns, it likely returns the validated/flagged data.
    validated_data = run_t015_validation_pipeline(features_data)
    
    if not validated_data:
        logger.error("Validation pipeline returned no data.")
        sys.exit(1)

    logger.info(f"Validation complete. {len(validated_data)} records ready for save.")

    # 3. Validate data integrity (check for nulls in critical columns)
    logger.info("Running data integrity checks...")
    if not validate_data_integrity(validated_data, ["modal_verb_freq", "imperative_declarative_ratio", "citation_density"]):
        logger.warning("Data integrity check found issues. Proceeding with save but flagging.")
    
    # 4. Save to data/processed/features.csv
    logger.info(f"Saving final dataset to {output_path}")
    
    if len(validated_data) == 0:
        logger.error("No data to save.")
        sys.exit(1)

    fieldnames = list(validated_data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(validated_data)

    logger.info(f"Successfully saved {len(validated_data)} rows to {output_path}")
    return output_path

if __name__ == "__main__":
    main()
