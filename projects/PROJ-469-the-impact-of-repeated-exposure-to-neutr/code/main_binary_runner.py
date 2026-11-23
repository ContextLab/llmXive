import sys
from pathlib import Path
from binary_model import run_binary_model_pipeline
from logging_config import setup_logging, get_logger

def main():
    """Entry point for running the binary model pipeline."""
    logger = setup_logging()
    logger.info("Starting Binary Model Pipeline Execution")
    
    try:
        results = run_binary_model_pipeline()
        logger.info(f"Binary Model Pipeline Completed Successfully. Results: {results}")
        return 0
    except Exception as e:
        logger.error(f"Binary Model Pipeline Failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())