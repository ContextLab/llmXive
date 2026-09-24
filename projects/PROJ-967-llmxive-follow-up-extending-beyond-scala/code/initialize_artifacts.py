import argparse
import json
import logging
import os
import sys
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def initialize_empty_artifacts(base_path: str):
    """
    Initialize the required output artifacts with empty/default content.
    
    Creates:
    - data/processed/features.json: initialized as an empty list []
    - results/results.json: initialized as an empty dict {}
    """
    base = Path(base_path)
    
    # Ensure directories exist
    processed_dir = base / "data" / "processed"
    results_dir = base / "results"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize features.json
    features_path = processed_dir / "features.json"
    with open(features_path, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)
    logging.info(f"Initialized {features_path} with empty list []")
    
    # Initialize results.json
    results_path = results_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
    logging.info(f"Initialized {results_path} with empty dict {{}}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Initialize output artifacts for llmXive pipeline"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
        help="Base path for the project (default: projects/PROJ-967-llmxive-follow-up-extending-beyond-scala)"
    )
    return parser.parse_args()

def main():
    setup_logging()
    args = parse_args()
    initialize_empty_artifacts(args.base_path)
    logging.info("Artifact initialization complete.")

if __name__ == "__main__":
    main()
