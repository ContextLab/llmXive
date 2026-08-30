"""
Script to download and install the required spaCy model.
Implements Task T011a-3.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import download_spacy_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for downloading the spaCy model.
    """
    logger.info("Starting spaCy model download...")
    try:
        download_spacy_model()
        logger.info("spaCy model setup completed successfully.")
    except Exception as e:
        logger.error(f"Failed to setup spaCy model: {e}")
        raise

if __name__ == "__main__":
    main()