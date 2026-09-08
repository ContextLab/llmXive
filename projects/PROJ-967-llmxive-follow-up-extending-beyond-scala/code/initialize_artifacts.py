import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def initialize_empty_artifacts(logger):
    """
    Initialize empty output artifacts to prevent file-not-found errors in downstream tasks.
    
    Artifacts created:
    - data/processed/features.json: Initialized as an empty list []
    - results/results.json: Initialized as an empty object {}
    """
    # Define the project root relative to this script's location
    # The script is in code/, so project root is two levels up
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define paths relative to project root
    features_path = project_root / "data" / "processed" / "features.json"
    results_path = project_root / "results" / "results.json"
    
    # Ensure directories exist
    features_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize features.json with empty list
    logger.info(f"Initializing {features_path} with empty list []")
    with open(features_path, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)
    
    # Initialize results.json with empty object
    logger.info(f"Initializing {results_path} with empty object {{}}")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)
    
    logger.info("Output artifacts initialized successfully.")
    return True

def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize empty output artifacts for the pipeline."
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    try:
        initialize_empty_artifacts(logger)
        return 0
    except Exception as e:
        logger.error(f"Failed to initialize artifacts: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
