"""
T017: Generate standardized CSV output with checksums.

This script reads the preprocessed data (from T016), ensures it meets the
schema defined in contracts/dataset.schema.yaml (verified in T005),
writes it to data/processed/standardized.csv, and generates a SHA-256
checksum file.

Dependencies:
  - preprocess.py (run_preprocessing_pipeline)
  - config.py (get_data_dir)
"""
import hashlib
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_data_dir
from preprocess import run_preprocessing_pipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'participant_id',
    'stimulus_sequence',
    'duration_estimate',
    'surprisal'
]

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_schema(df: pd.DataFrame) -> bool:
    """Validate that the DataFrame contains required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"Schema validation failed. Missing columns: {missing}")
        return False
    return True

def run_t017():
    """Execute the standardized output generation."""
    logger.info("Starting T017: Generate standardized CSV output.")
    
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_csv_path = processed_dir / "standardized.csv"
    checksum_path = processed_dir / "standardized.csv.sha256"
    
    # 1. Run preprocessing pipeline to ensure data is ready
    # This calls the logic from T015/T016
    logger.info("Running preprocessing pipeline to prepare data...")
    df_preprocessed = run_preprocessing_pipeline()

    if df_preprocessed is None or df_preprocessed.empty:
        logger.error("Preprocessing pipeline returned no data. Aborting T017.")
        return False

    # 2. Validate Schema
    logger.info(f"Validating schema for {len(df_preprocessed)} rows...")
    if not validate_schema(df_preprocessed):
        logger.error("Data does not match required schema. Aborting.")
        return False

    # 3. Ensure column order matches specification
    df_standardized = df_preprocessed[REQUIRED_COLUMNS].copy()

    # 4. Write to CSV
    logger.info(f"Writing standardized CSV to {output_csv_path}...")
    df_standardized.to_csv(output_csv_path, index=False)

    # 5. Compute and write checksum
    logger.info(f"Computing checksum for {output_csv_path}...")
    checksum = compute_sha256(output_csv_path)
    
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  standardized.csv\n")
    
    logger.info(f"Checksum generated: {checksum}")
    logger.info(f"T017 Complete. Output: {output_csv_path}, Checksum: {checksum_path}")
    
    return True

if __name__ == "__main__":
    success = run_t017()
    sys.exit(0 if success else 1)
