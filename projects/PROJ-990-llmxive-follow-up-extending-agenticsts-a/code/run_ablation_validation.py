import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

from ablation import main as run_ablation_main
from t008d_ablation_failure_handler import main as run_ablation_failure_handler_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Orchestrates the ablation study (T008) and the failure handling (T008d).
    1. Runs T008.
    2. If T008 fails, runs T008d.
    """
    logger.info("Starting Ablation Validation Phase (T008 + T008d)")
    
    try:
        # Run T008
        run_ablation_main()
        logger.info("T008 completed successfully.")
    except Exception as e:
        logger.error(f"T008 failed with error: {e}")
        logger.info("Triggering T008d (Failure Handling)...")
        try:
            run_ablation_failure_handler_main()
        except Exception as e2:
            logger.critical(f"T008d failed: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main()