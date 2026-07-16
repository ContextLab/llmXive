"""
Hyperparameter Logging Module

This module handles the logging and management of hyperparameter search results.
It reads the hyperparameter log generated during training, formats entries for
readability, and provides functionality to regenerate the log from training results.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import setup_logging, get_logger

# Constants
HYPERPARAMETER_LOG_PATH = "artifacts/hyperparameter_search.log"
TRAINING_RESULTS_PATH = "artifacts/training_results.json"
BEST_MODEL_PATH = "artifacts/best_model.pt"
METRICS_PATH = "artifacts/metrics.json"

def load_hyperparameter_log(log_path: str = HYPERPARAMETER_LOG_PATH) -> List[Dict[str, Any]]:
    """
    Load the hyperparameter search log from a JSON file.

    Args:
        log_path: Path to the hyperparameter log file

    Returns:
        List of dictionaries containing hyperparameter configurations and scores
    """
    path = Path(log_path)
    if not path.exists():
        logger = get_logger(__name__)
        logger.warning(f"Hyperparameter log not found at {log_path}")
        return []

    with open(path, 'r') as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected log format at {log_path}, expected list")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse hyperparameter log: {e}")
            return []

def format_hyperparameter_entry(entry: Dict[str, Any], max_width: int = 80) -> str:
    """
    Format a single hyperparameter entry for logging to file.

    Args:
        entry: Dictionary containing hyperparameters and scores
        max_width: Maximum width for the formatted string

    Returns:
        Formatted string representation of the entry
    """
    lines = []
    lines.append("-" * max_width)

    # Extract key metrics
    config = entry.get('config', {})
    metrics = entry.get('metrics', {})

    # Header with validation score
    val_score = metrics.get('val_r2', float('nan'))
    val_mae = metrics.get('val_mae', float('nan'))
    lines.append(f"Config {entry.get('config_id', 'N/A')}: Val R²={val_score:.4f}, Val MAE={val_mae:.4f}")

    # Hyperparameters
    lines.append("Hyperparameters:")
    for key, value in sorted(config.items()):
        if isinstance(value, float):
            lines.append(f"  {key}: {value:.4f}")
        else:
            lines.append(f"  {key}: {value}")

    # Training metrics
    lines.append("Training Metrics:")
    for key, value in sorted(metrics.items()):
        if key not in ['config']:
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.4f}")
            else:
                lines.append(f"  {key}: {value}")

    lines.append("")
    return "\n".join(lines)

def generate_hyperparameter_log(
    results_path: str = TRAINING_RESULTS_PATH,
    output_path: str = HYPERPARAMETER_LOG_PATH
) -> List[Dict[str, Any]]:
    """
    Generate the hyperparameter search log from training results.

    This function reads the training results JSON, extracts the hyperparameter
    configurations and their corresponding validation scores, and writes them
    to the log file in a human-readable format.

    Args:
        results_path: Path to the training results JSON file
        output_path: Path where the log file should be written

    Returns:
        List of hyperparameter entries
    """
    logger = get_logger(__name__)

    # Ensure output directory exists
    ensure_dirs()

    # Load training results
    if not Path(results_path).exists():
        logger.error(f"Training results not found at {results_path}")
        # Create a placeholder log if no results exist
        with open(output_path, 'w') as f:
            f.write("# No training results found\n")
        return []

    with open(results_path, 'r') as f:
        results = json.load(f)

    # Ensure results is a list
    if not isinstance(results, list):
        logger.error(f"Expected list of results in {results_path}, got {type(results)}")
        return []

    # Sort results by validation R² (descending)
    sorted_results = sorted(
        results,
        key=lambda x: x.get('metrics', {}).get('val_r2', float('-inf')),
        reverse=True
    )

    # Write formatted log
    with open(output_path, 'w') as f:
        f.write(f"# Hyperparameter Search Results\n")
        f.write(f"# Total configurations tested: {len(sorted_results)}\n")
        f.write(f"# Best validation R²: {sorted_results[0].get('metrics', {}).get('val_r2', 'N/A'):.4f}\n")
        f.write(f"# Generated from: {results_path}\n")
        f.write("#" + "=" * 79 + "\n\n")

        for i, entry in enumerate(sorted_results):
            # Add rank
            entry['rank'] = i + 1
            formatted = format_hyperparameter_entry(entry)
            f.write(formatted)

    logger.info(f"Hyperparameter log written to {output_path}")
    return sorted_results

def main(args=None):
    """
    Main entry point for the hyperparameter logging script.

    Usage:
        python -m models.log_hyperparameters --results artifacts/training_results.json
    """
    parser = argparse.ArgumentParser(
        description="Generate hyperparameter search log from training results"
    )
    parser.add_argument(
        '--results',
        type=str,
        default=TRAINING_RESULTS_PATH,
        help=f"Path to training results JSON (default: {TRAINING_RESULTS_PATH})"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=HYPERPARAMETER_LOG_PATH,
        help=f"Path for output log file (default: {HYPERPARAMETER_LOG_PATH})"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )

    parsed_args = parser.parse_args(args)

    # Setup logging
    log_level = logging.DEBUG if parsed_args.verbose else logging.INFO
    setup_logging(level=log_level)

    logger = get_logger(__name__)
    logger.info("Starting hyperparameter log generation")

    try:
        results = generate_hyperparameter_log(
            results_path=parsed_args.results,
            output_path=parsed_args.output
        )

        if results:
            logger.info(f"Successfully logged {len(results)} hyperparameter configurations")
            # Print top 5 to console
            logger.info("Top 5 configurations:")
            for entry in results[:5]:
                val_r2 = entry.get('metrics', {}).get('val_r2', 0)
                config = entry.get('config', {})
                logger.info(f"  {entry.get('rank')}: R²={val_r2:.4f} - {config}")
        else:
            logger.warning("No hyperparameter configurations found in results")

        return 0

    except Exception as e:
        logger.error(f"Failed to generate hyperparameter log: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())