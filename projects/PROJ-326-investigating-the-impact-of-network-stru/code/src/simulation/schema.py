"""
Schema definitions and validation for simulation results.
Ensures that simulation results conform to the expected structure
and contain all required fields.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)


class SchemaError(Exception):
    """Exception raised for schema validation errors."""
    pass


def get_schema() -> Dict[str, Any]:
    """
    Get the complete JSON schema for the simulation results file.

    Returns:
        Dictionary representing the JSON schema.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SimulationResults",
        "description": "Schema for simulation results containing diffusion metrics",
        "type": "array",
        "items": {
            "$ref": "#/definitions/SimulationRun"
        },
        "definitions": {
            "SimulationRun": {
                "type": "object",
                "required": [
                    "network_id",
                    "seed",
                    "diffusion_rate",
                    "topology_class"
                ],
                "properties": {
                    "network_id": {
                        "type": "string",
                        "description": "Unique identifier for the network"
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed used for the simulation"
                    },
                    "diffusion_rate": {
                        "type": "number",
                        "description": "Calculated diffusion rate from the simulation"
                    },
                    "topology_class": {
                        "type": "string",
                        "description": "Class of network topology (e.g., Erdos-Renyi, Watts-Strogatz, Barabasi-Albert)"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "ISO 8601 timestamp of when the simulation was run"
                    },
                    "num_nodes": {
                        "type": "integer",
                        "description": "Number of nodes in the network"
                    },
                    "num_edges": {
                        "type": "integer",
                        "description": "Number of edges in the network"
                    },
                    "clustering_coefficient": {
                        "type": "number",
                        "description": "Average clustering coefficient of the network"
                    },
                    "average_path_length": {
                        "type": "number",
                        "description": "Average shortest path length in the network"
                    }
                },
                "additionalProperties": False
            }
        }
    }


def get_results_schema() -> Dict[str, Any]:
    """
    Get the schema for a single simulation run result.

    Returns:
        Dictionary representing the schema for a single result.
    """
    schema = get_schema()
    return schema["definitions"]["SimulationRun"]


def validate_simulation_run(result: Dict[str, Any]) -> bool:
    """
    Validate a single simulation run result against the schema.

    Args:
        result: Dictionary containing a single simulation run result.

    Returns:
        True if valid.

    Raises:
        SchemaError: If validation fails.
    """
    schema = get_results_schema()
    required_fields = schema["required"]

    # Check for required fields
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        raise SchemaError(
            f"Missing required fields in simulation result: {missing_fields}"
        )

    # Type checking for required fields
    if not isinstance(result["network_id"], str):
        raise SchemaError(
            f"network_id must be a string, got {type(result['network_id']).__name__}"
        )

    if not isinstance(result["seed"], int):
        raise SchemaError(
            f"seed must be an integer, got {type(result['seed']).__name__}"
        )

    if not isinstance(result["diffusion_rate"], (int, float)):
        raise SchemaError(
            f"diffusion_rate must be a number, got {type(result['diffusion_rate']).__name__}"
        )

    if not isinstance(result["topology_class"], str):
        raise SchemaError(
            f"topology_class must be a string, got {type(result['topology_class']).__name__}"
        )

    # Optional fields type checking
    if "timestamp" in result and not isinstance(result["timestamp"], str):
        raise SchemaError(
            f"timestamp must be a string, got {type(result['timestamp']).__name__}"
        )

    if "num_nodes" in result and not isinstance(result["num_nodes"], int):
        raise SchemaError(
            f"num_nodes must be an integer, got {type(result['num_nodes']).__name__}"
        )

    if "num_edges" in result and not isinstance(result["num_edges"], int):
        raise SchemaError(
            f"num_edges must be an integer, got {type(result['num_edges']).__name__}"
        )

    if "clustering_coefficient" in result and not isinstance(
        result["clustering_coefficient"], (int, float)
    ):
        raise SchemaError(
            f"clustering_coefficient must be a number, "
            f"got {type(result['clustering_coefficient']).__name__}"
        )

    if "average_path_length" in result and not isinstance(
        result["average_path_length"], (int, float)
    ):
        raise SchemaError(
            f"average_path_length must be a number, "
            f"got {type(result['average_path_length']).__name__}"
        )

    # Check for additional properties not in schema
    allowed_keys = set(schema["properties"].keys())
    result_keys = set(result.keys())
    extra_keys = result_keys - allowed_keys
    if extra_keys:
        raise SchemaError(
            f"Unexpected fields in simulation result: {extra_keys}"
        )

    return True


def validate_results_file(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate a complete results file (list of results) against the schema.

    Args:
        data: The data to validate (should be a list of dictionaries).
        schema: The schema to validate against.

    Returns:
        True if valid.

    Raises:
        SchemaError: If validation fails.
    """
    if not isinstance(data, list):
        raise SchemaError(
            f"Expected a list of results, got {type(data).__name__}"
        )

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise SchemaError(
                f"Item at index {i} is not a dictionary, got {type(item).__name__}"
            )
        validate_simulation_run(item)

    return True


def save_results(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save simulation results to a JSON file with schema validation.

    Args:
        results: List of simulation result dictionaries.
        output_path: Optional path to save the results. Defaults to
            data/analysis/simulation_results.json.

    Returns:
        Path to the saved file.

    Raises:
        SchemaError: If validation fails.
        IOError: If unable to write to the specified path.
    """
    if output_path is None:
        output_path = Path("data/analysis/simulation_results.json")

    # Ensure the output directory exists
    ensure_data_directory(output_path)

    # Validate results
    schema = get_schema()
    validate_results_file(results, schema)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved {len(results)} simulation results to {output_path}")
    return output_path


def load_results(
    input_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Load simulation results from a JSON file and validate against schema.

    Args:
        input_path: Optional path to load results from. Defaults to
            data/analysis/simulation_results.json.

    Returns:
        List of simulation result dictionaries.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        SchemaError: If validation fails.
    """
    if input_path is None:
        input_path = Path("data/analysis/simulation_results.json")

    if not input_path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate loaded data
    schema = get_schema()
    validate_results_file(data, schema)

    logger.info(f"Loaded {len(data)} simulation results from {input_path}")
    return data
