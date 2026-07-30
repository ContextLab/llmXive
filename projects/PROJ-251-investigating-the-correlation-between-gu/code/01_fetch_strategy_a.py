import os
import sys
import logging
from pathlib import Path
from utils.sra_fetcher import main as fetch_main
from utils.logging_config import get_logger, log_error_context

def main():
    """
    Strategy A: Fetch pre-processed OTU table and serology metadata.
    
    This script retrieves the specific dataset identified by config.SRA_ACCESSION.
    It expects the data to be available via a verified real source (e.g., HuggingFace
    or a direct URL provided in the config). If the fetch fails, it raises
    DataUnavailableError to halt the pipeline.
    
    Output:
        data/raw/otutable.csv
        data/raw/serology.csv
    """
    logger = get_logger(__name__)
    logger.info("Starting Strategy A: Fetch pre-processed data")
    
    try:
        # Delegate to the fetcher which handles the actual download logic
        # based on the verified real source configuration.
        fetch_main()
        
        logger.info("Strategy A completed successfully. Files written to data/raw/")
        
    except Exception as e:
        log_error_context(logger, "Failed to fetch data", e)
        # Re-raise to ensure the pipeline halts on failure
        raise

if __name__ == "__main__":
    main()
