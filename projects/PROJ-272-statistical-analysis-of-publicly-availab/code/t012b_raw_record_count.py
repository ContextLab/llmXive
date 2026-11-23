import json
import logging
import os
from pathlib import Path
import pandas as pd
from config import get_path

from ingestion import count_raw_records

def main():
    """
    Entry point for T012b: Raw Record Count & Group Counts.
    This script calls the count_raw_records function from ingestion.py
    to perform the counting and save the results.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting T012b: Raw Record Count & Group Counts")
    
    # Execute the counting logic
    try:
        count_raw_records()
        logger.info("T012b completed successfully.")
    except Exception as e:
        logger.error(f"T012b failed: {e}")
        raise

if __name__ == "__main__":
    main()
