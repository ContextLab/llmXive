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

def initialize_empty_artifacts(base_path: Path, logger: logging.Logger):
    """
    Initialize empty output artifacts to prevent file-not-found errors in downstream tasks.
    
    Artifacts created:
    - data/processed/features.json: Empty list []
    - results/results.json: Empty object {}
    """
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Initialize features.json with empty list
    features_path = processed_dir / "features.json"
    with open(features_path, 'w', encoding='utf-8') as f:
        json.dump([], f)
    logger.info(f"Initialized {features_path} with empty list []")

    # Initialize results.json with empty object
    results_path = results_dir / "results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({}, f)
    logger.info(f"Initialized {results_path} with empty object {{}}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize empty output artifacts for the pipeline."
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base path to the project directory."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    base_path = Path(args.base_path)

    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)

    initialize_empty_artifacts(base_path, logger)
    logger.info("Artifact initialization completed successfully.")

if __name__ == "__main__":
    main()
