"""
Task T027c: Save placeholder model when training is skipped (e.g., N < 30).

This script handles the edge case where the dataset is too small for
meaningful model training. It writes a placeholder pickle file and
a results JSON to satisfy SC-001 and allow the pipeline to continue
gracefully without crashing.
"""

import argparse
import json
import logging
import os
import pickle
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Save a placeholder model when training is skipped."
    )
    parser.add_argument(
        "--output-model",
        type=str,
        default="results/model.pkl",
        help="Path to the output model pickle file."
    )
    parser.add_argument(
        "--output-results",
        type=str,
        default="results/results.json",
        help="Path to the output results JSON file."
    )
    parser.add_argument(
        "--reason",
        type=str,
        default="N < 30, correlation unmeasurable",
        help="Reason for skipping training."
    )
    return parser.parse_args()


def save_placeholder_model(output_path: str, reason: str):
    """
    Save a placeholder model object to a pickle file.

    Args:
        output_path: Path to the output pickle file.
        reason: The reason why training was skipped.
    """
    metadata = {
        "status": "no_data",
        "message": reason
    }

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(output_path, 'wb') as f:
        pickle.dump(metadata, f)

    logger.info(f"Saved placeholder model to {output_path}")


def save_results_placeholder(output_path: str, reason: str):
    """
    Save a placeholder results JSON file.

    Args:
        output_path: Path to the output JSON file.
        reason: The reason why training was skipped.
    """
    results = {
        "status": "no_data",
        "message": reason,
        "model_type": "none",
        "n_samples": 0,
        "metrics": {}
    }

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved placeholder results to {output_path}")


def main():
    """Main entry point for the placeholder model saving script."""
    args = parse_args()

    logger.info(f"Saving placeholder model due to: {args.reason}")

    # Save the placeholder model
    save_placeholder_model(args.output_model, args.reason)

    # Save the placeholder results
    save_results_placeholder(args.output_results, args.reason)

    logger.info("Placeholder artifacts saved successfully.")


if __name__ == "__main__":
    main()