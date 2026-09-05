"""
Task T001e: Initialize output artifacts.

Creates empty placeholder files to prevent file-not-found errors in downstream tasks:
- data/processed/features.json (initialized to [])
- results/results.json (initialized to {})
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def initialize_empty_artifacts(base_path: Path, logger: logging.Logger):
    """
    Initialize the required empty artifact files.

    Args:
        base_path: The root directory of the project.
        logger: Logger instance.
    """
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Define artifact paths
    features_path = processed_dir / "features.json"
    results_path = results_dir / "results.json"

    # Initialize features.json
    try:
        with open(features_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        logger.info(f"Initialized {features_path} with empty list.")
    except Exception as e:
        logger.error(f"Failed to initialize {features_path}: {e}")
        raise

    # Initialize results.json
    try:
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        logger.info(f"Initialized {results_path} with empty dict.")
    except Exception as e:
        logger.error(f"Failed to initialize {results_path}: {e}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize output artifacts for T001e.")
    parser.add_argument(
        "--project-root",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Path to the project root directory."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    base_path = Path(args.project_root)

    if not base_path.exists():
        logger.error(f"Project root does not exist: {base_path}")
        sys.exit(1)

    initialize_empty_artifacts(base_path, logger)
    logger.info("T001e: Output artifacts initialized successfully.")

if __name__ == "__main__":
    main()
