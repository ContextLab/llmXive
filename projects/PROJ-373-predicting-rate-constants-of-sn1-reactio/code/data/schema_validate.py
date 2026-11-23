import os
import sys
import logging
from pathlib import Path

# Import logger setup from existing utility
from utils.logger import get_logger
from config import DataConfig

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

def setup_validation_logger():
    """Setup logging for schema validation."""
    logger = get_logger('schema_validate', 'data/processed/schema_validate.log')
    return logger

def read_pipeline_status(status_path: Path) -> str:
    """
    Read the pipeline status file.
    Returns the content stripped of whitespace.
    Returns 'MISSING' if the file does not exist.
    """
    if not status_path.exists():
        return 'MISSING'
    
    try:
        content = status_path.read_text().strip()
        return content
    except Exception as e:
        logging.error(f"Failed to read pipeline status: {e}")
        return 'ERROR_READ'

def write_pipeline_status(status_path: Path, status: str):
    """Write the status to the pipeline status file."""
    try:
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(status)
        logging.info(f"Wrote status '{status}' to {status_path}")
    except Exception as e:
        logging.error(f"Failed to write pipeline status: {e}")
        raise

def fetch_dataset_metadata_for_freshness_check():
    """
    Re-fetch dataset metadata from HuggingFace to verify columns exist *now*.
    This implements the 'Freshness Check' constraint.
    
    Returns:
        bool: True if metadata is valid (columns exist), False otherwise.
    """
    try:
        from datasets import load_dataset
        
        # Use the verified dataset IDs from T011a/Spec
        # We only need to check the schema, so we stream just the info
        # We check the first dataset mentioned in the spec/plan: DTS-SN1-15-01-2024
        # Note: If the dataset name is not public or requires auth, this might fail.
        # However, the task requires a real check.
        
        required_columns = ['substrate_class', 'temperature', 'solvent']
        
        # Attempt to load just the info (streaming=True avoids full download)
        # We try the primary source first. If it fails, we try the secondary.
        # The spec mentions: DTS-SN1-15-01-2024 and SN18-All-20240204
        
        dataset_names = [
            "DTS-SN1-15-01-2024", 
            "SN18-All-20240204"
        ]
        
        for ds_name in dataset_names:
            try:
                # We don't need to download the whole dataset, just check the columns
                # load_dataset with streaming=True and split='train' will fetch the config info
                ds = load_dataset(ds_name, split='train', streaming=True, revision='main')
                
                # Check if the columns exist in the features
                # In streaming mode, we can check the feature names
                if hasattr(ds, 'features') and ds.features:
                    columns = list(ds.features.keys())
                    if all(col in columns for col in required_columns):
                        logging.info(f"FRESHNESS CHECK PASSED: Dataset '{ds_name}' has required columns.")
                        return True
                    else:
                        logging.warning(f"Dataset '{ds_name}' missing columns. Found: {columns}")
                else:
                    # If features are not immediately available in streaming, try to peek
                    # This is a heuristic; if we can't verify, we assume failure for safety
                    logging.warning(f"Could not verify columns for '{ds_name}' via streaming features.")
                    
            except Exception as e:
                logging.warning(f"Could not check dataset '{ds_name}': {e}")
                continue
        
        # If we get here, no dataset passed the check
        logging.error("FRESHNESS CHECK FAILED: No verified dataset source contains required columns.")
        return False
        
    except Exception as e:
        logging.error(f"Error during freshness check metadata fetch: {e}")
        return False

def validate_schema_check_result(logger: logging.Logger) -> bool:
    """
    Validates the result of the schema check (T011a) with a Freshness Check.
    
    Logic:
    1. Re-fetch metadata from HuggingFace to verify columns exist *now* (Freshness Check).
    2. If missing columns in metadata -> overwrite status to 'ABORTED' and exit with code 1.
    3. If metadata is valid, read `data/processed/.pipeline_status`.
    4. If file is *missing*, treat this as T011a failure (fatal error), write 'ABORTED', and exit with code 1.
    5. If contains 'ABORTED' or is not 'OK', exit with code 1.
    6. If 'OK', proceed.
    
    Returns True if validation passes, False otherwise.
    """
    config = DataConfig()
    status_path = config.processed_dir / '.pipeline_status'
    
    logger.info("Starting Freshness Check (re-fetching metadata)...")
    
    # Step 1: Freshness Check
    is_fresh = fetch_dataset_metadata_for_freshness_check()
    
    if not is_fresh:
        logger.error("Freshness check failed: Metadata missing or columns not found.")
        # Overwrite status to ABORTED
        write_pipeline_status(status_path, 'ABORTED')
        return False
    
    logger.info("Freshness check passed. Columns verified.")
    
    # Step 2: Read existing status
    logger.info(f"Checking pipeline status at: {status_path}")
    status = read_pipeline_status(status_path)
    
    if status == 'MISSING':
        logger.error("Pipeline status file (.pipeline_status) is MISSING. "
                     "This indicates T011a (schema_check) failed or was not run.")
        # Write ABORTED to ensure downstream tasks know the state
        write_pipeline_status(status_path, 'ABORTED')
        return False
    
    if status != 'OK':
        logger.error(f"Pipeline status is '{status}', expected 'OK'. "
                     "The upstream schema check failed or was aborted.")
        # Write ABORTED if not already
        if status != 'ABORTED':
            write_pipeline_status(status_path, 'ABORTED')
        return False
    
    logger.info("Pipeline status is 'OK'. Proceeding with data download.")
    return True

def main():
    """Main entry point for schema validation."""
    logger = setup_validation_logger()
    logger.info("Starting schema validation (T011b)...")
    
    try:
        if validate_schema_check_result(logger):
            logger.info("Schema validation passed. Exiting with code 0.")
            sys.exit(0)
        else:
            logger.error("Schema validation failed. Exiting with code 1.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        # Ensure we write ABORTED on unexpected crash
        try:
            config = DataConfig()
            write_pipeline_status(config.processed_dir / '.pipeline_status', 'ABORTED')
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()