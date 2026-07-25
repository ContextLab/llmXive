import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    """Configure logging for the artifact initialization process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def initialize_empty_artifacts(logger: logging.Logger):
    """
    Create empty output artifacts to prevent file-not-found errors in downstream tasks.
    
    Specifically:
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json (with [])
    - projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json (with {})
    """
    # Define the base project path
    base_path = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    # Define artifact paths relative to the base path
    features_path = base_path / "data" / "processed" / "features.json"
    results_path = base_path / "results" / "results.json"
    
    # Ensure parent directories exist
    features_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Ensuring directory exists: {features_path.parent}")
    logger.info(f"Ensuring directory exists: {results_path.parent}")
    
    # Initialize features.json with an empty list
    logger.info(f"Initializing {features_path} with empty list []")
    with open(features_path, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)
    
    # Initialize results.json with an empty object
    logger.info(f"Initializing {results_path} with empty object {{}}")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)
    
    logger.info("Artifact initialization complete.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize empty output artifacts for the pipeline."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    return parser.parse_args()

def main():
    """Main entry point for artifact initialization."""
    args = parse_args()
    logger = setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        initialize_empty_artifacts(logger)
    except Exception as e:
        logger.error(f"Failed to initialize artifacts: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
