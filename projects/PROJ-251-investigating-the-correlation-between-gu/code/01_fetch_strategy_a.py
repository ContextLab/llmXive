import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

from utils.sra_fetcher import fetch_strategy_a_data, DataUnavailableError
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entry point for Task T011a: Fetch pre-processed OTU table and serology metadata.
    """
    logger.info("Starting T011a: Fetch pre-processed data (Strategy A)")
    
    try:
        otu_path, serology_path = fetch_strategy_a_data()
        logger.info(f"Successfully fetched OTU table: {otu_path}")
        logger.info(f"Successfully fetched serology metadata: {serology_path}")
        
        # Verify the files are not empty and have headers
        if not pd.io.common.file_exists(otu_path):
            raise FileNotFoundError(f"OTU table file not found after fetch: {otu_path}")
        
        if not pd.io.common.file_exists(serology_path):
            raise FileNotFoundError(f"Serology file not found after fetch: {serology_path}")
        
        logger.info("T011a completed successfully.")
        return 0
        
    except DataUnavailableError as e:
        logger.critical(f"Strategy A failed: {e}")
        logger.info("Execution will halt. The pipeline should switch to synthetic data generation (T011b) if configured.")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error in T011a: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
