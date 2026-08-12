"""
T017 Execution Script: Run the preprocessing pipeline to generate batch-corrected data.

This script executes the `code/data/preprocess.py` pipeline to generate:
- data/processed/batch_corrected_matrix.csv
- data/processed/labels.csv

It also verifies file existence, non-empty content, and logs checksums to
state/artifact_hashes.yaml via utils.io.log_artifact.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess import main as run_preprocessing_main
from utils.io import compute_file_hash, log_artifact
from utils.constants import DATA_PROCESSED_DIR, STATE_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting T017: Executing preprocessing pipeline...")
    
    # Ensure output directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Execute the main preprocessing logic
    # This function is expected to download/verify data if not present,
    # or load from data/raw, process it, and save to DATA_PROCESSED_DIR.
    try:
        logger.info("Calling preprocess.main()...")
        run_preprocessing_main()
        logger.info("Preprocessing main function completed.")
    except Exception as e:
        logger.error(f"Preprocessing execution failed: {e}")
        raise

    # 2. Verify artifacts
    matrix_path = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
    labels_path = DATA_PROCESSED_DIR / "labels.csv"
    
    artifacts_to_check = [matrix_path, labels_path]
    missing_files = []
    
    for path in artifacts_to_check:
        if not path.exists():
            missing_files.append(str(path))
            logger.error(f"Missing expected artifact: {path}")
        elif path.stat().st_size == 0:
            missing_files.append(str(path))
            logger.error(f"Artifact exists but is empty: {path}")
        else:
            logger.info(f"Verified artifact: {path} (size: {path.stat().st_size} bytes)")

    if missing_files:
        raise FileNotFoundError(f"Required artifacts missing or empty: {missing_files}")

    # 3. Log checksums to state/artifact_hashes.yaml
    logger.info("Computing checksums and logging artifacts...")
    for path in artifacts_to_check:
        file_hash = compute_file_hash(str(path), algorithm="sha256")
        log_artifact(
            path=str(path),
            hash_value=file_hash,
            artifact_type="processed_data"
        )
        logger.info(f"Logged artifact: {path} -> SHA256: {file_hash}")

    logger.info("T017 Execution completed successfully.")

if __name__ == "__main__":
    main()
