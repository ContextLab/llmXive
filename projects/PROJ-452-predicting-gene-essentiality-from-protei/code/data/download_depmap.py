"""
Script to download DepMap (DepMap) essentiality labels.
This script is invoked by the quickstart run-book.
It delegates to the main data_loader module.
Note: DepMap is primarily for cancer cell lines, but included for completeness
if the pipeline is extended to include cancer essentiality data.
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
    Downloads DepMap essentiality labels.
    Note: This script currently uses the same fetch_essentiality_labels function
    as DEG, but in a real implementation, this would connect to DepMap API/FTP.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting DepMap essentiality labels download script.")
    
    try:
        organisms = get_organisms()
        
        logger.info(f"Organisms to process: {organisms}")
        
        for organism_id in organisms:
            logger.info(f"Processing organism: {organism_id}")
            try:
                # Placeholder: In a real implementation, this would fetch from DepMap
                # For now, it attempts to fetch from DEG (as DepMap integration is not yet implemented)
                logger.warning(f"  DepMap integration not yet implemented for {organism_id}. Skipping or using fallback.")
                
                # Attempt to fetch from DEG as a fallback for demonstration
                essentiality_data = fetch_essentiality_labels(organism_id)
                if essentiality_data is not None and len(essentiality_data) > 0:
                    logger.info(f"  Fetched {len(essentiality_data)} labels (from DEG fallback) for {organism_id}")
                else:
                    logger.warning(f"  No data available for {organism_id}")
            except Exception as e:
                logger.error(f"  Failed to fetch data for {organism_id}: {e}")
                    
        logger.info("DepMap essentiality labels download script completed.")
        
    except Exception as e:
        logger.critical(f"Fatal error in download script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()