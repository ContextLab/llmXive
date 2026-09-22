import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration for retry logic
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 30.0     # seconds

def setup_schema_check_logger() -> logging.Logger:
    """Setup logging for schema check."""
    return get_logger(__name__)

def fetch_dataset_info_with_retry(dataset_name: str, split: str = 'train') -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetch dataset info from HuggingFace with exponential backoff retry logic.
    Returns (features_dict, error_message).
    If successful, error_message is None. If failed after retries, features is None.
    """
    attempt = 0
    backoff = INITIAL_BACKOFF

    while attempt < MAX_RETRIES:
        try:
            from datasets import load_dataset
            logger.info(f"Fetching dataset info for {dataset_name} (attempt {attempt + 1}/{MAX_RETRIES})...")
            
            # Load with streaming=True to fetch metadata without full download
            dataset = load_dataset(dataset_name, split=split, streaming=True, revision='main')
            
            # Access features to trigger metadata fetch
            features = dataset.info.features
            if features:
                logger.info(f"Successfully fetched dataset info for {dataset_name}")
                return features, None
            else:
                raise ValueError("Dataset features returned empty or None")

        except Exception as e:
            attempt += 1
            if attempt >= MAX_RETRIES:
                error_msg = f"Failed to fetch dataset info for {dataset_name} after {MAX_RETRIES} attempts: {str(e)}"
                logger.error(error_msg)
                return None, error_msg
            
            # Exponential backoff
            sleep_time = min(backoff * (2 ** (attempt - 1)), MAX_BACKOFF)
            logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {sleep_time:.2f}s...")
            time.sleep(sleep_time)

    # Should not reach here due to loop logic, but safety return
    return None, f"Unexpected exit from retry loop for {dataset_name}"

def validate_columns(features: Dict[str, Any], required_columns: List[str]) -> List[str]:
    """
    Validate that required columns exist in dataset.
    Returns a list of missing columns. Empty list if all present.
    """
    missing_columns = []
    for col in required_columns:
        if col not in features:
            missing_columns.append(col)
    return missing_columns

def main():
    parser = argparse.ArgumentParser(description="Check dataset schema for SN1 reaction data")
    parser.add_argument("--dataset", type=str, default="author/DTS-SN1-15-01-2024", 
                        help="HuggingFace dataset name")
    parser.add_argument("--output", type=str, default="data/processed/schema_check.log", 
                        help="Output log path")
    parser.add_argument("--required-columns", nargs='+', default=[
        'smiles', 'rate_constant', 'substrate_class', 'temperature', 'solvent'
    ], help="Required columns to validate")
    args = parser.parse_args()

    ensure_dirs()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Fetch dataset info with retry logic
        features, error = fetch_dataset_info_with_retry(args.dataset)
        
        if error:
            # Fatal error: network issue or dataset not found
            logger.critical(f"Schema check halted: {error}")
            with open(args.output, 'w') as f:
                f.write(f"status: 'error'\n")
                f.write(f"reason: '{error}'\n")
                f.write("action: 'pipeline_halted'\n")
            raise ValueError(f"Schema check failed due to network/dataset error: {error}")

        # Validate required columns
        missing = validate_columns(features, args.required_columns)
        
        if missing:
            # Fatal error: missing required columns
            error_msg = f"Missing required columns: {missing}"
            logger.critical(f"Schema check halted: {error_msg}")
            with open(args.output, 'w') as f:
                f.write(f"status: 'fail'\n")
                f.write(f"reason: '{error_msg}'\n")
                f.write("action: 'pipeline_halted'\n")
            raise ValueError(error_msg)

        # Success
        logger.info("Schema validation passed for all required columns")
        with open(args.output, 'w') as f:
            f.write("status: 'pass'\n")
            f.write(f"dataset: {args.dataset}\n")
            f.write(f"columns_verified: {list(features.keys())}\n")
            f.write("action: 'proceed'\n")
        
        logger.info(f"Schema check log written to {args.output}")

    except ValueError as ve:
        # Re-raise to halt pipeline as per requirements
        raise ve
    except Exception as e:
        logger.critical(f"Unexpected error during schema check: {str(e)}")
        with open(args.output, 'w') as f:
            f.write(f"status: 'error'\n")
            f.write(f"reason: 'unexpected_exception: {str(e)}'\n")
            f.write("action: 'pipeline_halted'\n")
        raise e

if __name__ == "__main__":
    import argparse
    main()