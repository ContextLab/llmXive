import sys
import logging
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_logging import setup_logging, get_data_quality_logger
from validate_covariates import main as validate_main

def main():
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Running covariate validation task (T028e)")
    
    try:
        validate_main()
    except Exception as e:
        logger.error(f"Covariate validation failed: {e}")
        sys.exit(1)
    
    logger.info("Covariate validation completed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()