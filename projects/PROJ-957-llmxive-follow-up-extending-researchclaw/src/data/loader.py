"""
ResearchClawBench Data Loader

Fetches the ResearchClawBench dataset, computes checksums, and verifies integrity.
This module strictly adheres to real data sources and fails loudly if verification fails.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path to ensure imports work in various execution contexts
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from src.config import Config
from src.utils.logging import setup_logging, log_with_context, get_global_error_tracker
from src.utils.checksum import compute_sha256, write_checksum, read_checksum

# Initialize logging
logger = setup_logging("data_loader")

# Constants
CHECKSUM_FILE_PATH = "data/raw/checksum.txt"
RAW_DATA_DIR = "data/raw"
EXPECTED_CHECKSUM_KEY = "RESEARCHCLAWBENCH_EXPECTED_CHECKSUM"

def _compute_dataset_checksum(dataset) -> str:
    """
    Computes a deterministic SHA256 checksum of the dataset content.
    Since 'datasets' objects are complex, we serialize a canonical representation
    of the first N rows and schema to create a stable hash for verification.
    
    Note: For very large datasets, a full hash is expensive. We hash the 
    schema + a representative sample (e.g., first 1000 rows) to ensure 
    the data source and structure are correct.
    """
    hasher = hashlib.sha256()
    
    # 1. Hash the schema (column names and types)
    if hasattr(dataset, 'features'):
        schema_str = json.dumps(dataset.features, sort_keys=True)
        hasher.update(schema_str.encode('utf-8'))
    
    # 2. Hash the data (sample)
    # We take the first 1000 rows to ensure the data content is verified
    # without loading the entire dataset into memory for hashing if it's huge.
    # However, to be strictly deterministic and safe against truncation attacks,
    # we iterate. For this task, we assume the dataset ID is stable.
    
    # Convert to list of dicts for the sample
    sample_size = 1000
    try:
        # If streaming, we need to materialize the sample
        if dataset.is_streaming:
            sample_data = []
            for i, row in enumerate(dataset):
                if i >= sample_size:
                    break
                sample_data.append(row)
        else:
            sample_data = dataset.select(range(min(sample_size, len(dataset)))).to_list()
        
        # Canonical JSON serialization
        canonical_str = json.dumps(sample_data, sort_keys=True, separators=(',', ':'))
        hasher.update(canonical_str.encode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to sample dataset for checksum: {e}")
        raise e

    return hasher.hexdigest()

def load_researchclawbench() -> Any:
    """
    Loads the ResearchClawBench dataset.
    
    1. Reads the dataset ID from Config.
    2. Loads the dataset using the 'datasets' library.
    3. Computes a checksum of the loaded data.
    4. Writes the checksum to data/raw/checksum.txt.
    5. If the computed checksum does not match the expected one (from config/env),
       it triggers the Verified Accuracy Gate (T007b) logic by raising an error.
    
    Returns:
        The loaded HuggingFace Dataset object.
    
    Raises:
        RuntimeError: If the dataset ID is invalid or checksum verification fails.
    """
    config = Config.load()
    dataset_id = config.RESEARCHCLAWBENCH_DATASET_ID
    
    logger.info(f"Loading dataset: {dataset_id}")
    
    # Ensure output directory exists
    raw_dir = project_root / RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load dataset
        # We use trust_remote_code=True if needed, but standard datasets usually don't need it.
        # We load in streaming mode to avoid OOM on large datasets, but for checksum
        # we need to materialize a sample.
        dataset = load_dataset(dataset_id, split="train", streaming=False)
        
        # Compute checksum
        checksum = _compute_dataset_checksum(dataset)
        logger.info(f"Computed checksum: {checksum}")
        
        # Write checksum to file
        checksum_path = raw_dir / "checksum.txt"
        write_checksum(str(checksum_path), checksum)
        logger.info(f"Checksum written to {checksum_path}")
        
        # Verify against expected checksum if defined in config
        expected_checksum = getattr(config, 'RESEARCHCLAWBENCH_EXPECTED_CHECKSUM', None)
        
        if expected_checksum:
            if checksum != expected_checksum:
                error_msg = (
                    f"CHECKSUM MISMATCH: Expected {expected_checksum}, got {checksum}. "
                    "Triggering Verified Accuracy Gate (T007b). Aborting."
                )
                logger.error(error_msg)
                # The task description says to "trigger the Verified Accuracy Gate".
                # In a real system, this might call a specific gate function.
                # Here, we raise an error which will be caught by the execution controller
                # or the gate logic (T007b) if it were a separate step. 
                # Since T007b is a separate task, we raise an exception to stop execution.
                raise RuntimeError(error_msg)
            else:
                logger.info("Checksum verification passed.")
        else:
            logger.warning("No expected checksum defined in config. Skipping verification.")
        
        return dataset
        
    except Exception as e:
        logger.error(f"Failed to load or verify dataset: {e}")
        # If the dataset ID is invalid, datasets.load_dataset will raise a specific error.
        # We ensure we fail loudly.
        raise e

def main():
    """
    Entry point for running the loader as a script.
    This is useful for manual verification or CI pre-checks.
    """
    try:
        logger.info("Starting ResearchClawBench Loader...")
        dataset = load_researchclawbench()
        logger.info(f"Successfully loaded dataset with {len(dataset)} rows.")
        logger.info("Loader completed successfully.")
        return 0
    except RuntimeError as e:
        # This covers the checksum mismatch and dataset ID errors
        logger.critical(f"Loader failed: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
