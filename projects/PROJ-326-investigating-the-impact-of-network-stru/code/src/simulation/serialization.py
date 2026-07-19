"""
Serialization module for simulation results.
Handles saving and loading simulation results to/from JSON files.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.simulation.schema import validate_simulation_run, get_results_schema
from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)

def save_simulation_result(
    result: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a single simulation result to a JSON file.

    Args:
        result: Dictionary containing simulation result data.
        output_path: Optional path to save the result. If None, uses default path.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If the result does not match the expected schema.
    """
    # Validate result against schema
    schema = get_results_schema()
    if not validate_simulation_run(result, schema):
        raise ValueError(f"Result does not match expected schema: {result}")

    # Ensure output directory exists
    if output_path is None:
        output_path = Path("data/analysis/simulation_results.json")
    else:
        output_path = Path(output_path)

    ensure_data_directory(output_path.parent)

    # If file exists, load existing results and append
    existing_results = []
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                existing_results = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing results from {output_path}: {e}")
            existing_results = []

    # Append new result
    existing_results.append(result)

    # Write updated results
    with open(output_path, 'w') as f:
        json.dump(existing_results, f, indent=2, default=str)

    logger.info(f"Saved simulation result to {output_path}")
    return output_path

def save_batch_results(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a batch of simulation results to a single JSON file.

    Args:
        results: List of dictionaries containing simulation result data.
        output_path: Optional path to save the results. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = Path("data/analysis/simulation_results.json")
    else:
        output_path = Path(output_path)

    ensure_data_directory(output_path.parent)

    # Validate each result
    schema = get_results_schema()
    validated_results = []
    for i, result in enumerate(results):
        if validate_simulation_run(result, schema):
            validated_results.append(result)
        else:
            logger.warning(f"Skipping invalid result at index {i}: {result}")

    # Write results
    with open(output_path, 'w') as f:
        json.dump(validated_results, f, indent=2, default=str)

    logger.info(f"Saved {len(validated_results)} simulation results to {output_path}")
    return output_path

def load_simulation_results(
    input_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Load simulation results from a JSON file.

    Args:
        input_path: Optional path to load results from. If None, uses default path.

    Returns:
        List of simulation result dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = Path("data/analysis/simulation_results.json")
    else:
        input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")

    with open(input_path, 'r') as f:
        results = json.load(f)

    logger.info(f"Loaded {len(results)} simulation results from {input_path}")
    return results

def main(args: Optional[Any] = None) -> int:
    """
    Main entry point for the serialization script.
    Can be used to test serialization functionality or as a standalone script.

    Args:
        args: Optional command-line arguments namespace.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Serialization script for simulation results")
    parser.add_argument("--output", type=str, default="data/analysis/simulation_results.json",
                      help="Output path for simulation results")
    parser.add_argument("--test", action="store_true",
                      help="Run test serialization")
    parser.add_argument("--load", type=str, default=None,
                      help="Path to load results from")

    parsed_args = parser.parse_args(args) if args else parser.parse_args()

    try:
        if parsed_args.test:
            # Create a test result
            test_result = {
                "network_id": "test_network_001",
                "seed": 42,
                "diffusion_rate": 0.123,
                "topology_class": "watts_strogatz",
                "steps_run": 100,
                "status": "SUCCESS",
                "runtime_duration_seconds": 1.234,
                "generation_algorithm": "watts_strogatz",
                "parameter_values": {
                    "n": 100,
                    "k": 4,
                    "p": 0.1
                }
            }

            output_path = Path(parsed_args.output)
            save_simulation_result(test_result, output_path)
            logger.info(f"Test result saved to {output_path}")

            # Verify by loading
            loaded_results = load_simulation_results(output_path)
            logger.info(f"Loaded {len(loaded_results)} results for verification")

        elif parsed_args.load:
            # Load and display results
            results = load_simulation_results(Path(parsed_args.load))
            logger.info(f"Loaded {len(results)} results from {parsed_args.load}")
            for i, result in enumerate(results):
                logger.info(f"Result {i}: {result.get('network_id', 'N/A')} - {result.get('status', 'N/A')}")

        else:
            parser.print_help()
            return 1

        return 0

    except Exception as e:
        logger.error(f"Serialization failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
