"""
Main entry point for data ingestion pipeline.
Orchestrates T012a (NREL) and T012b (MP) fetches.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fetch_nrel_perovskites import main as fetch_nrel_main
from fetch_mp_perovskites import main as fetch_mp_main
from merge_datasets import main as merge_main
from data_ingestion_metadata import main as metadata_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_data():
    """
    Placeholder for loading raw data if needed before processing.
    Currently, fetchers handle their own I/O.
    """
    return None

def validate_entries(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates entries based on schema.
    """
    valid = []
    invalid = []
    # Basic validation logic
    for item in data:
        if "formula" in item and "T_d" in item:
            valid.append(item)
        else:
            invalid.append(item)
    return valid, invalid

def parse_and_enrich(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parses and enriches data with additional metadata.
    """
    return data

def main():
    logger.info("Starting Data Ingestion Pipeline")
    
    # Run NREL Fetch (T012a)
    logger.info("Running T012a: NREL Fetch")
    try:
        fetch_nrel_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("NREL Fetch failed. Aborting.")
            sys.exit(1)

    # Run MP Fetch (T012b)
    logger.info("Running T012b: Materials Project Fetch")
    try:
        fetch_mp_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Materials Project Fetch failed. Aborting.")
            sys.exit(1)

    # Run Merge (T012c)
    logger.info("Running T012c: Merge Datasets")
    try:
        merge_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Merge failed. Aborting.")
            sys.exit(1)

    # Run Metadata Extraction (T013)
    logger.info("Running T013: Metadata Extraction")
    try:
        metadata_main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("Metadata extraction failed. Aborting.")
            sys.exit(1)

    logger.info("Data Ingestion Pipeline completed successfully.")

if __name__ == "__main__":
    main()
