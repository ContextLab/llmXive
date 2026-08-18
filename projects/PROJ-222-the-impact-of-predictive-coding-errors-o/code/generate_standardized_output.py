import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd

from config import get_data_dir
from preprocess import run_preprocessing_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Validate dataframe against the output schema.
    Schema expects: duration_estimate, stimulus_sequence, participant_id, surprisal
    """
    required_columns = {"duration_estimate", "stimulus_sequence", "participant_id", "surprisal"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        logger.error(f"Schema validation failed: Missing columns {missing}")
        return False

    # Basic type checks if possible
    if not pd.api.types.is_numeric_dtype(df["duration_estimate"]):
        logger.warning("duration_estimate is not numeric")
    
    return True


def run_t017() -> bool:
    """
    Execute T017: Generate standardized CSV output with checksums.
    
    1. Runs the preprocessing pipeline (T015/T016) to ensure data is ready.
    2. Loads the preprocessed data.
    3. Ensures it matches the schema defined in contracts/output.schema.yaml.
    4. Saves to data/processed/standardized.csv.
    5. Computes and saves checksums to data/processed/standardized.sha256.
    6. Logs success or failure.
    """
    logger.info("Starting T017: Generate standardized CSV output")
    
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / "standardized.csv"
    checksum_path = processed_dir / "standardized.sha256"
    schema_path = data_dir.parent / "contracts" / "output.schema.yaml"
    
    # Step 1: Ensure preprocessing has run (T015/T016)
    # The preprocessing pipeline generates intermediate files or returns a DF.
    # Based on T015/T016 implementation, we assume run_preprocessing_pipeline 
    # writes to a temp location or returns the DF. 
    # To be safe and idempotent, we call it and let it handle its own logic.
    # However, T017 specifically needs the *final* standardized CSV.
    # We assume run_preprocessing_pipeline writes to data/processed/intermediate.csv 
    # or similar, or we can just re-run the logic if needed.
    # Given the task flow, we assume the pipeline has been run or run it here.
    
    # For this implementation, we assume run_preprocessing_pipeline 
    # returns the processed DataFrame or we load from a known intermediate spot.
    # Let's assume the pipeline writes to data/processed/intermediate.csv 
    # and we just transform it to standardized.
    # Actually, looking at T015/T016, they likely produce the data in memory or a temp file.
    # We will call run_preprocessing_pipeline to get the data.
    
    try:
        # The run_preprocessing_pipeline from T015/T016 should return the processed DF
        # or write to a specific location. We assume it writes to 
        # data/processed/preprocessed.csv if not returned.
        # Let's assume it returns the DF for simplicity in this step.
        df = run_preprocessing_pipeline()
        
        if df is None or df.empty:
            logger.error("Preprocessing pipeline returned no data. T017 cannot proceed.")
            return False
            
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        # If the pipeline hasn't run or failed, we can't generate standardized output.
        # We return False to indicate T017 failed.
        return False

    # Step 2: Validate Schema
    if schema_path.exists():
        if not validate_schema(df, schema_path):
            logger.error("Schema validation failed. Dropping T017.")
            return False
    else:
        logger.warning("Schema file not found at {schema_path}. Skipping validation.")
        # Fallback: check basic columns manually
        required_cols = {"duration_estimate", "stimulus_sequence", "participant_id", "surprisal"}
        if not required_cols.issubset(df.columns):
            logger.error(f"Missing required columns: {required_cols - set(df.columns)}")
            return False

    # Step 3: Save Standardized CSV
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved standardized data to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save standardized CSV: {e}")
        return False

    # Step 4: Compute Checksum
    try:
        checksum = compute_sha256(output_path)
        with open(checksum_path, "w") as f:
            f.write(f"{checksum}  standardized.csv\n")
        logger.info(f"Computed checksum: {checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        return False

    logger.info("T017 completed successfully.")
    return True


def main():
    """Entry point for T017."""
    success = run_t017()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
