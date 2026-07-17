"""
Serialization utilities for simulation results.
Handles saving and loading simulation data to/from JSON files.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.simulation.schema import validate_simulation_run, get_results_schema
from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)

def save_simulation_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Save a single simulation result to a JSON file.

    Args:
        result: Dictionary containing simulation results
        output_path: Path to the output JSON file
    """
    ensure_data_directory(output_path)

    # Validate against schema before saving
    schema = get_results_schema()
    if not validate_simulation_run(result, schema):
        raise ValueError(f"Result validation failed: {result}")

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    logger.info(f"Saved simulation result to {output_path}")

def save_batch_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save a batch of simulation results to a JSON file.

    Args:
        results: List of dictionaries containing simulation results
        output_path: Path to the output JSON file
    """
    ensure_data_directory(output_path)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Saved {len(results)} simulation results to {output_path}")

def load_simulation_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load simulation results from a JSON file.

    Args:
        input_path: Path to the input JSON file

    Returns:
        List of dictionaries containing simulation results
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")

    with open(input_path, 'r') as f:
        results = json.load(f)

    logger.info(f"Loaded {len(results)} simulation results from {input_path}")
    return results

def main():
    """CLI entry point for serialization module."""
    import argparse
    parser = argparse.ArgumentParser(description="Simulation serialization utilities")
    parser.add_argument("--action", choices=["save", "load"], required=True, help="Action to perform")
    parser.add_argument("--input", type=str, help="Input file path")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--data", type=str, help="JSON data to save (for save action)")

    args = parser.parse_args()

    if args.action == "save":
        if not args.output:
            parser.error("--output required for save action")
        if not args.data:
            parser.error("--data required for save action")

        result = json.loads(args.data)
        save_simulation_result(result, Path(args.output))
        print(f"Saved to {args.output}")

    elif args.action == "load":
        if not args.input:
            parser.error("--input required for load action")

        results = load_simulation_results(Path(args.input))
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
