import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def initialize_empty_artifacts(base_path: Path, logger: logging.Logger):
    """
    Initialize empty output artifacts to prevent file-not-found errors in downstream tasks.
    
    Creates:
    - data/processed/features.json with content []
    - results/results.json with content {}
    """
    processed_dir = base_path / "data" / "processed"
    results_dir = base_path / "results"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize features.json
    features_path = processed_dir / "features.json"
    try:
        with open(features_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        logger.info(f"Initialized empty features.json at {features_path}")
    except IOError as e:
        logger.error(f"Failed to write features.json: {e}")
        raise
    
    # Initialize results.json
    results_path = results_dir / "results.json"
    try:
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        logger.info(f"Initialized empty results.json at {results_path}")
    except IOError as e:
        logger.error(f"Failed to write results.json: {e}")
        raise

def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize empty output artifacts for the llmXive pipeline."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        required=True,
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
    
    try:
        initialize_empty_artifacts(base_path, logger)
        logger.info("Artifact initialization completed successfully.")
    except Exception as e:
        logger.error(f"Artifact initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
