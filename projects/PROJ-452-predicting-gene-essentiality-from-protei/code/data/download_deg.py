"""
Script to download DEG (Database of Essential Genes) essentiality labels.
This script is invoked by the quickstart run-book.
It delegates to the main data_loader module.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import fetch_essentiality_labels
from config import get_organisms
from utils import setup_logging

def main():
    """
    Downloads essentiality labels for configured organisms.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting DEG essentiality labels download script.")
    
    try:
        organisms = get_organisms()
        
        logger.info(f"Organisms to process: {organisms}")
        
        for organism_id in organisms:
            logger.info(f"Processing organism: {organism_id}")
            try:
                # This will attempt to fetch from DEG FTP/API
                # If it fails, it raises DataFetchError (handled in data_loader)
                essentiality_data = fetch_essentiality_labels(organism_id)
                if essentiality_data is not None and len(essentiality_data) > 0:
                    logger.info(f"  Successfully fetched {len(essentiality_data)} essentiality labels for {organism_id}")
                else:
                    logger.warning(f"  No essentiality data returned for {organism_id}")
            except Exception as e:
                logger.error(f"  Failed to fetch essentiality labels for {organism_id}: {e}")
                    
        logger.info("DEG essentiality labels download script completed.")
        
    except Exception as e:
        logger.critical(f"Fatal error in download script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
