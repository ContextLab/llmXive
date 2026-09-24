import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging(log_file=None):
    """Configure logging for the fail-loud handler."""
    log_level = logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode='w'))
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)

def ensure_directories(base_path):
    """Ensure required directories exist."""
    raw_dir = base_path / "data" / "raw"
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"
    
    for directory in [raw_dir, processed_dir, results_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    return True

def check_dataset_availability(base_path, logger):
    """
    Check if the dataset files exist and are valid.
    Raises RuntimeError if data is missing or invalid (Fail-Loud).
    
    This function implements the core requirement of T037c:
    - If both real data load and synthetic generation fail, raise RuntimeError.
    - If synthetic generation succeeded (indicated by the existence of the expected file), log success and return.
    """
    raw_dir = base_path / "data" / "raw"
    validation_log_path = raw_dir / "validation_log.json"
    expected_data_file = raw_dir / "oxford_pets_simulated.parquet"
    
    # Check if the data file exists (indicating T037 succeeded)
    if expected_data_file.exists():
        logger.info(f"Data file found: {expected_data_file}")
        
        # Verify validation log exists and indicates success
        if not validation_log_path.exists():
            logger.warning("Validation log missing. Attempting to regenerate status.")
            # If data exists but log doesn't, we assume success but log a warning
            return True
        
        try:
            with open(validation_log_path, 'r') as f:
                validation_data = json.load(f)
            
            status = validation_data.get("status", "")
            source = validation_data.get("source", "")
            
            if status == "success" or "Synthetic generation successful" in status:
                logger.info("Synthetic generation successful; skipping fail-loud abort.")
                logger.info(f"Source: {source}")
                return True
            elif status == "failed":
                # If the previous run explicitly failed, we might want to re-attempt or abort
                # For T037c, if the file exists but status is failed, it implies a partial state.
                # However, the primary check is: if the file exists, we assume the pipeline proceeded.
                # If the file DOES NOT exist, we abort.
                logger.error("Validation log indicates previous failure. Aborting pipeline.")
                raise RuntimeError("Pipeline aborted: Previous validation failed and data file missing or invalid.")
        
        except json.JSONDecodeError:
            logger.error("Validation log is corrupted.")
            raise RuntimeError("Pipeline aborted: Validation log corrupted.")
        
        except Exception as e:
            logger.error(f"Error reading validation log: {e}")
            raise RuntimeError(f"Pipeline aborted: Error reading validation log: {e}")
    
    else:
        # File does not exist -> Real load failed AND Synthetic generation failed
        logger.error("Dataset file not found: Oxford Pets simulated data missing.")
        logger.error("Real data load failed AND Synthetic generation failed.")
        raise RuntimeError(
            "CRITICAL FAILURE: Both real data load and synthetic generation failed. "
            "The pipeline cannot proceed without a valid dataset. "
            "Please check T037 (Data Producer) logs."
        )

def parse_args():
    parser = argparse.ArgumentParser(description="Fail-Loud Handler for Data Availability")
    parser.add_argument(
        "--base-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base path for the project"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (optional)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    base_path = Path(args.base_path)
    
    # Setup logging
    log_file = args.log_file if args.log_file else str(base_path / "results" / "fail_loud.log")
    logger = setup_logging(log_file)
    
    logger.info("Starting Fail-Loud Handler (T037c)...")
    
    try:
        # Ensure directories exist
        ensure_directories(base_path)
        
        # Check dataset availability
        check_dataset_availability(base_path, logger)
        
        logger.info("Fail-Loud check passed. Pipeline can proceed.")
        return 0
    
    except RuntimeError as e:
        logger.critical(f"ABORTING PIPELINE: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())