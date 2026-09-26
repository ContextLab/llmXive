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

def validate_schema_check_result(logger: logging.Logger) -> bool:
    """
    Validates the result of the schema check (T011a).
    
    Logic:
    1. Read `data/processed/.pipeline_status`.
    2. If missing -> treat as T011a failure (fatal error).
    3. If 'ABORTED' or not 'OK' -> exit with code 1.
    4. If 'OK' -> proceed.
    
    Returns True if validation passes, False otherwise.
    """
    config = DataConfig()
    status_path = config.processed_dir / '.pipeline_status'
    
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
        sys.exit(1)

if __name__ == "__main__":
    main()