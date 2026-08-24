import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import yaml

from config import get_data_dir
from preprocess import run_preprocessing_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Validate dataframe columns against the output schema.
    Returns True if valid, raises ValueError otherwise.
    """
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}, skipping validation.")
        return True

    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    required_columns = schema.get('required_columns', [])
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Standardized output missing required columns: {missing_columns}")

    logger.info(f"Schema validation passed. Found {len(df.columns)} columns.")
    return True


def run_t017():
    """
    T017 Implementation: Generate standardized CSV output in data/processed/standardized.csv with checksums.

    1. Runs the preprocessing pipeline to get the processed dataframe.
    2. Validates against the contract schema.
    3. Saves to data/processed/standardized.csv.
    4. Computes SHA256 checksum and saves to data/processed/standardized.csv.sha256.
    5. Logs the operation to data/processed/standardized_output.log.
    """
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_path = processed_dir / "standardized.csv"
    checksum_path = processed_dir / "standardized.csv.sha256"
    schema_path = data_dir.parent / "contracts" / "output.schema.yaml"

    logger.info("Starting T017: Generating standardized CSV output...")

    # 1. Run preprocessing pipeline to get the data
    # Note: run_preprocessing_pipeline is expected to return the processed DataFrame
    # or handle its own internal state. Based on the API surface, we assume it returns the df.
    # If it returns None or handles side-effects internally, we adapt.
    # Looking at typical patterns, we call it and assume it prepares the data.
    # However, to be safe and modular, we might need to load the last processed file if
    # run_preprocessing_pipeline doesn't return it directly.
    # Let's assume run_preprocessing_pipeline returns the final df as per standard practice.
    
    try:
        df_processed = run_preprocessing_pipeline()
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        raise

    if df_processed is None or df_processed.empty:
        raise ValueError("Preprocessing pipeline returned empty or None data. Cannot generate standardized output.")

    logger.info(f"Preprocessing complete. Dataset shape: {df_processed.shape}")

    # 2. Validate against schema
    validate_schema(df_processed, schema_path)

    # 3. Save to CSV
    # Ensure consistent column ordering if schema defines an order (optional but good practice)
    # For now, we just save as is after validation.
    df_processed.to_csv(output_path, index=False)
    logger.info(f"Saved standardized output to {output_path}")

    # 4. Compute and save checksum
    checksum = compute_sha256(output_path)
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    logger.info(f"Saved checksum to {checksum_path}: {checksum}")

    # 5. Log operation details
    log_entry = {
        "task_id": "T017",
        "timestamp": str(pd.Timestamp.now()),
        "output_file": str(output_path),
        "checksum": checksum,
        "row_count": len(df_processed),
        "column_count": len(df_processed.columns),
        "status": "success"
    }
    
    log_file = processed_dir / "standardized_output.log"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info("T017 completed successfully.")
    return output_path, checksum


def main():
    """Entry point for running T017 as a script."""
    try:
        run_t017()
    except Exception as e:
        logger.error(f"Task T017 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
