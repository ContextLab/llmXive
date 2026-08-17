"""
Wrapper script to calculate Halstead Volume for every Java file.

This script acts as the entry point for the Halstead Volume calculation pipeline.
It loads a list of Java file paths (typically from a manifest or previous step),
invokes the core logic from `src.metrics_halstead`, and saves the results
to a JSON file in the processed data directory.

Usage:
    python wrapper_halstead.py --input <path_to_file_list.json> --output <path_to_results.json>
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure the project root is in the path to allow imports from src
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.metrics_halstead import calculate_halstead_batch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_file_list(input_path: str) -> List[str]:
    """
    Loads a list of Java file paths from a JSON file.

    Args:
        input_path (str): Path to the JSON file containing the list of file paths.

    Returns:
        List[str]: A list of absolute file paths to Java files.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file content is not a list of strings.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Input JSON must contain a list of file paths, got {type(data)}")

    # Validate that all items are strings
    for item in data:
        if not isinstance(item, str):
            raise ValueError(f"All items in the input list must be strings. Found: {type(item)}")

    return data


def save_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the calculation results to a JSON file.

    Args:
        results (List[Dict[str, Any]]): List of dictionaries containing file path and metrics.
        output_path (str): Path to the output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")


def main() -> None:
    """
    Main entry point for the Halstead Volume wrapper.

    Parses command line arguments, loads the file list, calculates metrics,
    and saves the results.
    """
    parser = argparse.ArgumentParser(
        description="Calculate Halstead Volume for a list of Java files."
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to JSON file containing list of Java file paths.'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to save the results JSON file.'
    )
    parser.add_argument(
        '--batch-size', '-b',
        type=int,
        default=100,
        help='Number of files to process in a single batch (default: 100).'
    )

    args = parser.parse_args()

    try:
        logger.info(f"Loading file list from {args.input}")
        file_paths = load_file_list(args.input)
        logger.info(f"Loaded {len(file_paths)} files.")

        if not file_paths:
            logger.warning("No files found in the input list. Exiting.")
            # Save an empty results file to indicate completion with no data
            save_results([], args.output)
            return

        logger.info(f"Calculating Halstead metrics for {len(file_paths)} files...")
        
        # Call the batch processing function from src.metrics_halstead
        # This function handles the actual parsing and calculation
        results = calculate_halstead_batch(file_paths, batch_size=args.batch_size)

        logger.info(f"Calculated metrics for {len(results)} files.")

        logger.info(f"Saving results to {args.output}")
        save_results(results, args.output)

        logger.info("Halstead Volume calculation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid input data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()