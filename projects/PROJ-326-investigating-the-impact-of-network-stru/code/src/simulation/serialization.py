"""
Result serialization module for simulation outputs.

This module handles the serialization of simulation results to JSON,
ensuring compliance with the defined schema (T029a).
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.simulation.schema import validate_simulation_run, get_results_schema

logger = logging.getLogger(__name__)


def save_simulation_result(
    output_path: Path,
    network_id: str,
    seed: int,
    diffusion_rate: float,
    topology_class: str,
    additional_metrics: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save a single simulation result to JSON with schema validation.

    Args:
        output_path: Path to the output JSON file.
        network_id: Unique identifier for the network graph.
        seed: Random seed used for the simulation.
        diffusion_rate: Calculated diffusion rate from the simulation.
        topology_class: Class of the network topology (e.g., 'ErdosRenyi', 'WattsStrogatz').
        additional_metrics: Optional dictionary of additional metrics to include.
        metadata: Optional dictionary of metadata (timestamp, version, etc.).

    Returns:
        The path to the saved file.

    Raises:
        ValueError: If the constructed result fails schema validation.
        IOError: If the file cannot be written.
    """
    result = {
        "network_id": network_id,
        "seed": seed,
        "diffusion_rate": diffusion_rate,
        "topology_class": topology_class,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if additional_metrics:
        result["additional_metrics"] = additional_metrics

    if metadata:
        result["metadata"] = metadata
    else:
        result["metadata"] = {
            "schema_version": "1.0",
            "generated_by": "simulation_runner"
        }

    # Validate against schema before saving
    schema = get_results_schema()
    try:
        validate_simulation_run(result, schema)
    except Exception as e:
        logger.error(f"Simulation result failed schema validation: {e}")
        raise ValueError(f"Schema validation failed: {e}") from e

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Saved simulation result to {output_path}")
    return output_path


def save_batch_results(
    output_path: Path,
    results: List[Dict[str, Any]]
) -> Path:
    """
    Save a batch of simulation results to a single JSON file.

    Args:
        output_path: Path to the output JSON file.
        results: List of result dictionaries to save.

    Returns:
        The path to the saved file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    batch_data = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(results),
        "results": results
    }

    # Validate each result individually before saving the batch
    schema = get_results_schema()
    for i, res in enumerate(results):
        try:
            validate_simulation_run(res, schema)
        except Exception as e:
            logger.error(f"Result at index {i} failed schema validation: {e}")
            raise ValueError(f"Batch validation failed at index {i}: {e}") from e

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2)

    logger.info(f"Saved batch of {len(results)} results to {output_path}")
    return output_path


def load_simulation_results(input_path: Path) -> Dict[str, Any]:
    """
    Load simulation results from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        The loaded data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate loaded data
    schema = get_results_schema()
    # If it's a batch, validate each result
    if "results" in data:
        for i, res in enumerate(data["results"]):
            validate_simulation_run(res, schema)
    else:
        # Single result
        validate_simulation_run(data, schema)

    return data
