"""
Main entry point for the Early Life Stress Impact Analysis Pipeline.
Implements robust error handling, JSON logging, and custom exception propagation.
"""

import json
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

# Ensure we can import sibling modules
# Assuming this script runs from the project root or code directory
# The project structure places 'code' at the root of the project
# We add the parent directory of this file to sys.path if running as script
if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "code":
        project_root = script_dir.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

from data.loaders import load_csv, load_tsv
from config import LOG_DIR, DATA_PROCESSED_DIR, LOG_FILE_NAME

# --- Custom Exceptions ---

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataLoadError(PipelineError):
    """Raised when data loading fails."""
    pass

class ValidationError(PipelineError):
    """Raised when data validation fails."""
    pass

class AnalysisError(PipelineError):
    """Raised when analysis steps fail."""
    pass

# --- Logging Configuration ---

def setup_logging() -> logging.Logger:
    """
    Configures a logger that writes JSON-formatted logs to logs/pipeline.log.
    Returns the configured logger instance.
    """
    # Ensure log directory exists
    log_path = Path(LOG_DIR)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file_path = log_path / LOG_FILE_NAME

    # Create logger
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates in interactive environments
    if logger.hasHandlers():
        logger.handlers.clear()

    # File Handler with JSON Formatter
    # We use a custom formatter to output JSON
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "module": record.module,
                "function": record.funcName,
                "message": record.getMessage(),
            }
            
            # Add exception info if present
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            
            # Add extra fields if present
            if hasattr(record, 'details'):
                log_record["details"] = record.details

            return json.dumps(log_record)

    file_handler = logging.FileHandler(log_file_path, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)

    # Optional: Stream handler for console (standard format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    return logger

# --- Main Pipeline Logic ---

def run_pipeline(logger: logging.Logger) -> bool:
    """
    Executes the main pipeline steps with comprehensive error handling.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Pipeline started.")
        
        # Example Step 1: Data Loading (Demonstrating I/O error handling)
        # Note: This attempts to load a file that might not exist yet or be empty,
        # serving as a test for the error handling mechanism.
        input_file = DATA_PROCESSED_DIR / "cleaned_dataset.csv"
        
        if not input_file.exists():
            # If the file doesn't exist, we handle it gracefully but log it
            # In a real run, this might be a failure condition depending on requirements
            logger.warning(f"Input file {input_file} not found. Skipping data loading step.")
        else:
            logger.info(f"Loading data from {input_file}")
            try:
                # Using the imported loader
                df = load_csv(input_file)
                logger.info(f"Successfully loaded {len(df)} rows.")
            except Exception as e:
                # Specific handling for data loading errors
                error_msg = f"Failed to load data from {input_file}"
                logger.error(error_msg, extra={'details': {'error_type': type(e).__name__, 'details': str(e)}})
                raise DataLoadError(error_msg, details={'error_type': type(e).__name__, 'details': str(e)}) from e

        # Example Step 2: Validation (Demonstrating custom exception raising)
        # Simulate a check that might fail
        # In a real scenario, this would validate against schema
        logger.info("Running validation checks...")
        
        # Placeholder for actual validation logic
        # If validation fails, raise ValidationError
        # For now, we assume it passes if data loaded
        
        logger.info("Pipeline completed successfully.")
        return True

    except DataLoadError as e:
        logger.critical(f"Data loading failed: {e.message}", extra={'details': e.details})
        return False
    except ValidationError as e:
        logger.critical(f"Validation failed: {e.message}", extra={'details': e.details})
        return False
    except AnalysisError as e:
        logger.critical(f"Analysis failed: {e.message}", extra={'details': e.details})
        return False
    except Exception as e:
        # Catch-all for unexpected errors
        logger.critical(f"Unexpected error occurred: {str(e)}", exc_info=True)
        return False

def main():
    """Entry point for the script."""
    logger = setup_logging()
    success = run_pipeline(logger)
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
