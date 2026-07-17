"""
Serialization module for simulation results.
Handles saving and loading simulation results to/from JSON files
with schema validation.
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
    output_path: str
) -> None:
    """
    Save a single simulation result to a JSON file with schema validation.

    Args:
        result: Dictionary containing simulation result data with fields:
            - network_id: str
            - seed: int
            - diffusion_rate: float
            - topology_class: str
            - steps_run: int
            - status: str
        output_path: Path to the output JSON file.

    Raises:
        ValueError: If the result does not conform to the schema.
        IOError: If writing to the file fails.
    """
    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    ensure_data_directory(output_dir)

    # Validate the result against the schema
    schema = get_results_schema()
    try:
        validate_simulation_run(result, schema)
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # Add metadata
    result_with_metadata = result.copy()
    result_with_metadata['saved_at'] = datetime.now(timezone.utc).isoformat()

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result_with_metadata, f, indent=2)
        logger.info(f"Saved simulation result to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write result to {output_path}: {e}")
        raise


def save_batch_results(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save a batch of simulation results to a single JSON file.

    Args:
        results: List of dictionaries containing simulation result data.
        output_path: Path to the output JSON file.

    Raises:
        ValueError: If any result does not conform to the schema.
        IOError: If writing to the file fails.
    """
    if not results:
        logger.warning("No results to save.")
        return

    # Validate all results
    schema = get_results_schema()
    for i, result in enumerate(results):
        try:
            validate_simulation_run(result, schema)
        except ValueError as e:
            logger.error(f"Schema validation failed for result {i}: {e}")
            raise ValueError(f"Result {i} validation failed: {e}")

    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    ensure_data_directory(output_dir)

    # Add metadata to each result
    results_with_metadata = []
    for result in results:
        result_copy = result.copy()
        result_copy['saved_at'] = datetime.now(timezone.utc).isoformat()
        results_with_metadata.append(result_copy)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_with_metadata, f, indent=2)
        logger.info(f"Saved {len(results)} simulation results to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write results to {output_path}: {e}")
        raise


def load_simulation_results(
    input_path: str
) -> List[Dict[str, Any]]:
    """
    Load simulation results from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        List of dictionaries containing simulation result data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        ValueError: If the data does not conform to the schema.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {input_path}: {e}")
        raise

    # Ensure data is a list
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError(f"Expected list of results, got {type(data)}")

    # Validate each result
    schema = get_results_schema()
    for i, result in enumerate(data):
        try:
            validate_simulation_run(result, schema)
        except ValueError as e:
            logger.error(f"Schema validation failed for result {i}: {e}")
            raise ValueError(f"Result {i} validation failed: {e}")

    logger.info(f"Loaded {len(data)} simulation results from {input_path}")
    return data