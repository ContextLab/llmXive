import argparse
import json
import logging
import os
import pickle
import sys
from pathlib import Path

def setup_logging():
    """Configure logging for the placeholder model saving task."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Save a placeholder model when training is skipped due to insufficient data.'
    )
    parser.add_argument(
        '--model-output',
        type=str,
        default='results/model.pkl',
        help='Path to save the placeholder model pickle file.'
    )
    parser.add_argument(
        '--results-output',
        type=str,
        default='results/results.json',
        help='Path to save the results JSON file with failure status.'
    )
    parser.add_argument(
        '--reason',
        type=str,
        default='Critical Power Limitation: N < 30',
        help='Reason for skipping training.'
    )
    return parser.parse_args()

def save_placeholder_model(output_path: str, reason: str, logger: logging.Logger):
    """
    Save a placeholder model object to disk when training is skipped.

    Args:
        output_path: Path to the output pickle file.
        reason: The reason string explaining why training was skipped.
        logger: Logger instance for reporting.
    """
    metadata = {
        "status": "fail",
        "message": reason,
        "model_type": "fail",
        "reason": reason
    }

    try:
        # Ensure the directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Placeholder model saved to {output_path}")
        logger.info(f"Content: {metadata}")
    except Exception as e:
        logger.error(f"Failed to save placeholder model to {output_path}: {e}")
        raise

def save_results_placeholder(output_path: str, reason: str, logger: logging.Logger):
    """
    Save the results JSON file indicating the pipeline failed at the training stage.

    Args:
        output_path: Path to the output JSON file.
        reason: The reason string explaining why training was skipped.
        logger: Logger instance for reporting.
    """
    results = {
        "status": "fail",
        "message": reason,
        "model_type": "fail",
        "reason": reason,
        "training_skipped": True
    }

    try:
        # Ensure the directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results placeholder saved to {output_path}")
        logger.info(f"Content: {results}")
    except Exception as e:
        logger.error(f"Failed to save results placeholder to {output_path}: {e}")
        raise

def main():
    """Main entry point for the placeholder model saving task."""
    logger = setup_logging()
    args = parse_args()

    logger.info("Starting placeholder model save process...")
    logger.info(f"Model output path: {args.model_output}")
    logger.info(f"Results output path: {args.results_output}")
    logger.info(f"Reason for skip: {args.reason}")

    # Save the placeholder model pickle
    save_placeholder_model(args.model_output, args.reason, logger)

    # Save the results JSON
    save_results_placeholder(args.results_output, args.reason, logger)

    logger.info("Placeholder model save process completed successfully.")

if __name__ == "__main__":
    main()
