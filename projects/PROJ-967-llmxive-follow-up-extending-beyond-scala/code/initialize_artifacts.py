import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    """Configure basic logging for the artifact initialization process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def initialize_empty_artifacts(output_features_path, output_results_path, logger):
    """
    Initialize the output artifacts with empty structures.
    
    Args:
        output_features_path (Path): Path to write features.json
        output_results_path (Path): Path to write results.json
        logger: Logger instance
    """
    # Ensure parent directories exist
    output_features_path.parent.mkdir(parents=True, exist_ok=True)
    output_results_path.parent.mkdir(parents=True, exist_ok=True)

    # Write empty features list
    with open(output_features_path, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)
    logger.info(f"Initialized empty features at: {output_features_path}")

    # Write empty results dict
    with open(output_results_path, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)
    logger.info(f"Initialized empty results at: {output_results_path}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize output artifacts (features.json and results.json) with empty structures."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Root directory of the project (default: current directory)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    
    project_root = Path(args.project_root)
    
    # Define paths relative to project root
    features_path = project_root / "data" / "processed" / "features.json"
    results_path = project_root / "results" / "results.json"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Target features path: {features_path}")
    logger.info(f"Target results path: {results_path}")

    try:
        initialize_empty_artifacts(features_path, results_path, logger)
        logger.info("Artifact initialization completed successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize artifacts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
