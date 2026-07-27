"""
Script to run the inference loop for T013a.
"""
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from inference import main as run_inference_main

def main():
    """Run inference loop with default or CLI arguments."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting inference run script")

    # Default arguments for T013a
    os.environ['INPUT_PATH'] = os.environ.get('INPUT_PATH', 'data/processed/filtered_splits.json')
    os.environ['OUTPUT_PATH'] = os.environ.get('OUTPUT_PATH', 'data/processed/convergence_results.csv')
    os.environ['TEMP_PATH'] = os.environ.get('TEMP_PATH', 'data/processed/temp_trajectory.json')

    # Run the main inference function
    run_inference_main()
    logger.info("Inference run completed")

if __name__ == '__main__':
    main()
