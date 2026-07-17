"""
Serialization module for simulation results.
Handles saving and loading of simulation results to/from JSON files,
ensuring schema compliance and data integrity.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.simulation.schema import validate_results_file, get_results_schema
from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)


def save_simulation_result(
    result: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a single simulation result to a JSON file.

    Args:
        result: Dictionary containing simulation results with keys:
            - network_id: str
            - seed: int
            - diffusion_rate: float
            - topology_class: str
            - timestamp: str (optional, auto-generated if missing)
        output_path: Optional path to save the result. If None, uses
            data/analysis/simulation_results.json.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If result is missing required fields or fails schema validation.
        IOError: If unable to write to the specified path.
    """
    if output_path is None:
        output_path = Path("data/analysis/simulation_results.json")

    # Ensure the output directory exists
    ensure_data_directory(output_path)

    # Validate the result against the schema
    schema = get_results_schema()
    validate_results_file(result, schema)

    # Add timestamp if not present
    if "timestamp" not in result:
        result["timestamp"] = datetime.now().isoformat()

    # If the file exists, load existing results, append, and save
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_results = json.load(f)
            if not isinstance(existing_results, list):
                logger.warning(
                    f"Existing file {output_path} is not a list. Overwriting."
                )
                existing_results = [existing_results]
            existing_results.append(result)
            final_data = existing_results
        except json.JSONDecodeError:
            logger.warning(
                f"Existing file {output_path} is corrupted. Overwriting."
            )
            final_data = [result]
    else:
        final_data = [result]

    # Write the final data to the file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    logger.info(f"Saved simulation result to {output_path}")
    return output_path


def save_batch_simulation_results(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a batch of simulation results to a JSON file.

    Args:
        results: List of dictionaries, each containing simulation results.
        output_path: Optional path to save the results. If None, uses
            data/analysis/simulation_results.json.

    Returns:
        Path to the saved file.

    Raises:
        ValueError: If any result fails schema validation.
        IOError: If unable to write to the specified path.
    """
    if output_path is None:
        output_path = Path("data/analysis/simulation_results.json")

    # Ensure the output directory exists
    ensure_data_directory(output_path)

    # Validate each result against the schema
    schema = get_results_schema()
    for i, result in enumerate(results):
        try:
            validate_results_file(result, schema)
        except ValueError as e:
            raise ValueError(f"Result at index {i} failed validation: {e}")

    # Add timestamps if not present
    for result in results:
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()

    # Load existing results if the file exists
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_results = json.load(f)
            if not isinstance(existing_results, list):
                logger.warning(
                    f"Existing file {output_path} is not a list. Overwriting."
                )
                existing_results = [existing_results]
            final_data = existing_results + results
        except json.JSONDecodeError:
            logger.warning(
                f"Existing file {output_path} is corrupted. Overwriting."
            )
            final_data = results
    else:
        final_data = results

    # Write the final data to the file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=2)

    logger.info(f"Saved {len(results)} simulation results to {output_path}")
    return output_path


def load_simulation_results(
    input_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Load simulation results from a JSON file.

    Args:
        input_path: Optional path to load results from. If None, uses
            data/analysis/simulation_results.json.

    Returns:
        List of dictionaries containing simulation results.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = Path("data/analysis/simulation_results.json")

    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        logger.warning(f"Loaded file {input_path} is not a list. Wrapping in list.")
        data = [data]

    logger.info(f"Loaded {len(data)} simulation results from {input_path}")
    return data


def append_single_result(
    result: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Append a single simulation result to an existing results file.
    This is a convenience wrapper around save_simulation_result.

    Args:
        result: Dictionary containing simulation results.
        output_path: Optional path to the results file.

    Returns:
        Path to the updated file.
    """
    return save_simulation_result(result, output_path)
