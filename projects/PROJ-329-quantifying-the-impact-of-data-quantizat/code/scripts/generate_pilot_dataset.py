import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_generation import main

def run():
    """
    Script wrapper to generate the pilot dataset.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Running pilot dataset generation script...")
    return main()

if __name__ == '__main__':
    sys.exit(run())
