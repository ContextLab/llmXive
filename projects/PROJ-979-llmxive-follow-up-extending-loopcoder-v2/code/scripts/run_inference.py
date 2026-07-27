"""
Script to run inference for convergence analysis.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.inference import main

def main():
    """
    Main entry point for the run_inference script.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Run the inference main function
        main()
        logger.info("Inference run completed successfully.")
    except Exception as e:
        logger.error(f"Error running inference: {e}")
        raise

if __name__ == "__main__":
    main()