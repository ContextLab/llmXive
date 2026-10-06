"""
Script to download STRING PPI networks.
This script is invoked by the quickstart run-book.
It delegates to the main data_loader module.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import fetch_string_network
from config import get_organisms, get_confidence_thresholds, load_config
from utils import setup_logging

def main():
    """
    Downloads STRING networks for configured organisms and thresholds.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting STRING network download script.")
    
    try:
        config = load_config()
        organisms = get_organisms(config)
        thresholds = get_confidence_thresholds(config)
        
        logger.info(f"Organisms to process: {organisms}")
        logger.info(f"Confidence thresholds: {thresholds}")
        
        for organism_id in organisms:
            logger.info(f"Processing organism: {organism_id}")
            for threshold in thresholds:
                logger.info(f"  Fetching network with threshold {threshold}...")
                try:
                    # This will attempt to fetch from STRING API
                    # If it fails, it raises DataFetchError (handled in data_loader)
                    network = fetch_string_network(organism_id, threshold)
                    if network is not None:
                        logger.info(f"  Successfully fetched network: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")
                    else:
                        logger.warning(f"  No network data returned for {organism_id} at threshold {threshold}")
                except Exception as e:
                    logger.error(f"  Failed to fetch network for {organism_id} at threshold {threshold}: {e}")
                    
        logger.info("STRING network download script completed.")
        
    except Exception as e:
        logger.critical(f"Fatal error in download script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
