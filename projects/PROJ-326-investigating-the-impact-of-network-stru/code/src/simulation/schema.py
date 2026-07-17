"""
Schema definitions and validation for simulation results.
Implements T029a: Define and validate JSON schema for simulation_results.json.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)

class SchemaError(Exception):
    """Exception raised for schema validation or loading errors."""
    pass

def get_schema() -> Dict[str, Any]:
    """
    Returns the JSON schema for a single SimulationRun entry.
    This matches the definition in contracts/simulation_run_schema.json.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SimulationRun",
        "description": "Schema for a single simulation run result entry as defined in US2.",
        "type": "object",
        "required": [
            "network_id",
            "seed",
            "diffusion_rate",
            "topology_class",
            "steps_run",
            "status"
        ],
        "properties": {
            "network_id": {
                "type": "string",
                "description": "Unique identifier for the network graph used in the simulation."
            },
            "seed": {
                "type": "integer",
                "description": "Random seed used for this specific simulation run."
            },
            "diffusion_rate": {
                "type": "number",
                "format": "float",
                "description": "Calculated rate of change of spatial variance (finite difference)."
            },
            "topology_class": {
                "type": "string",
                "description": "Class of the network topology (e.g., 'Erdos-Renyi', 'Watts-Strogatz', 'Barabasi-Albert')."
            },
            "steps_run": {
                "type": "integer",
                "description": "Number of time steps executed in the simulation."
            },
            "status": {
                "type": "string",
                "description": "Execution status of the simulation (e.g., 'SUCCESS', 'SIMULATION_DIVERGENCE', 'DISCONNECTED_NETWORK_FAILURE')."
            }
        },
        "additionalProperties": False
    }

def get_results_schema() -> Dict[str, Any]:
    """
    Returns the schema for the results file which is a list of SimulationRun objects.
    """
    schema = get_schema()
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SimulationResultsList",
        "type": "array",
        "items": schema
    }

def validate_simulation_run(record: Dict[str, Any]) -> bool:
    """
    Validates a single record against the SimulationRun schema.
    Raises SchemaError if validation fails.
    """
    schema = get_schema()
    required_fields = schema["required"]
    for field in required_fields:
        if field not in record:
            raise SchemaError(f"Missing required field: {field}")

    # Type checks
    if not isinstance(record["network_id"], str):
        raise SchemaError(f"network_id must be string, got {type(record['network_id'])}")
    if not isinstance(record["seed"], int):
        raise SchemaError(f"seed must be int, got {type(record['seed'])}")
    if not isinstance(record["diffusion_rate"], (int, float)):
        raise SchemaError(f"diffusion_rate must be float, got {type(record['diffusion_rate'])}")
    if not isinstance(record["topology_class"], str):
        raise SchemaError(f"topology_class must be string, got {type(record['topology_class'])}")
    if not isinstance(record["steps_run"], int):
        raise SchemaError(f"steps_run must be int, got {type(record['steps_run'])}")
    if not isinstance(record["status"], str):
        raise SchemaError(f"status must be string, got {type(record['status'])}")

    return True

def validate_results_file(file_path: Path) -> bool:
    """
    Validates the entire results file against the list schema.
    """
    if not file_path.exists():
        raise SchemaError(f"Results file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SchemaError(f"Results file must contain a JSON array, got {type(data)}")

    for i, record in enumerate(data):
        try:
            validate_simulation_run(record)
        except SchemaError as e:
            raise SchemaError(f"Validation failed for record {i}: {e}")

    return True

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves a list of simulation results to a JSON file, validating each entry first.
    """
    ensure_data_directory(output_path)

    # Validate all records before writing
    for i, record in enumerate(results):
        try:
            validate_simulation_run(record)
        except SchemaError as e:
            raise SchemaError(f"Failed to validate record {i} before saving: {e}")

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved {len(results)} simulation results to {output_path}")

def load_results(input_path: Path) -> List[Dict[str, Any]]:
    """
    Loads and validates simulation results from a JSON file.
    This function is imported by sensitivity.py and run_analysis.py.
    """
    if not input_path.exists():
        raise SchemaError(f"Results file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SchemaError(f"Results file must contain a JSON array, got {type(data)}")

    for i, record in enumerate(data):
        validate_simulation_run(record)

    return data