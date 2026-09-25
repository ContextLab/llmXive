import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    """Configure basic logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def initialize_empty_artifacts(base_dir: Path, logger: logging.Logger):
    """
    Initialize the required output artifacts with empty/default content.
    
    Creates:
    - data/processed/features.json with content []
    - results/results.json with content {}
    """
    data_processed_dir = base_dir / "data" / "processed"
    results_dir = base_dir / "results"

    # Ensure directories exist
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    features_path = data_processed_dir / "features.json"
    results_path = results_dir / "results.json"

    # Initialize features.json
    try:
        with open(features_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        logger.info(f"Initialized {features_path} with empty list []")
    except IOError as e:
        logger.error(f"Failed to write {features_path}: {e}")
        raise

    # Initialize results.json
    try:
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        logger.info(f"Initialized {results_path} with empty dict {{}}")
    except IOError as e:
        logger.error(f"Failed to write {results_path}: {e}")
        raise

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize empty output artifacts for the project."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base directory of the project (relative to repo root)."
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    logger = setup_logging()
    base_dir = Path(args.base_dir)

    if not base_dir.exists():
        logger.error(f"Base directory does not exist: {base_dir}")
        sys.exit(1)

    initialize_empty_artifacts(base_dir, logger)
    logger.info("Artifact initialization completed successfully.")

if __name__ == "__main__":
    main()
