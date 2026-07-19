import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)

class SchemaError(Exception):
    """Custom exception for schema validation errors."""
    pass

def get_schema() -> Dict[str, Any]:
    """
    Loads the SimulationRun schema from the contracts directory.
    """
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "simulation_run_schema.json"
    if not schema_path.exists():
        # Fallback to inline schema if file is missing during dev, though task T029a creates the file
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "SimulationRun",
            "type": "object",
            "required": [
                "network_id", "seed", "diffusion_rate", "topology_class",
                "steps_run", "status", "runtime_duration_seconds",
                "generation_algorithm", "parameter_values"
            ],
            "properties": {
                "network_id": {"type": "string"},
                "seed": {"type": "integer"},
                "diffusion_rate": {"type": "number"},
                "topology_class": {"type": "string"},
                "steps_run": {"type": "integer"},
                "status": {"type": "string"},
                "runtime_duration_seconds": {"type": "number"},
                "generation_algorithm": {"type": "string"},
                "parameter_values": {"type": "object"}
            }
        }
    
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid schema JSON at {schema_path}: {e}")

def get_results_schema() -> Dict[str, Any]:
    """
    Returns the schema for the simulation results file (list of SimulationRun).
    """
    base = get_schema()
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array",
        "items": base
    }

def validate_simulation_run(record: Dict[str, Any]) -> bool:
    """
    Validates a single record against the SimulationRun schema.
    Raises SchemaError if invalid.
    """
    schema = get_schema()
    
    # Check required fields
    required = schema.get("required", [])
    missing = [field for field in required if field not in record]
    if missing:
        raise SchemaError(f"Missing required fields: {missing}")
    
    # Type checking for critical fields
    if not isinstance(record.get("network_id"), str):
        raise SchemaError("network_id must be a string")
    if not isinstance(record.get("seed"), int):
        raise SchemaError("seed must be an integer")
    if not isinstance(record.get("diffusion_rate"), (int, float)):
        raise SchemaError("diffusion_rate must be a number")
    if not isinstance(record.get("steps_run"), int):
        raise SchemaError("steps_run must be an integer")
    if not isinstance(record.get("runtime_duration_seconds"), (int, float)):
        raise SchemaError("runtime_duration_seconds must be a number")
    if not isinstance(record.get("generation_algorithm"), str):
        raise SchemaError("generation_algorithm must be a string")
    if not isinstance(record.get("parameter_values"), dict):
        raise SchemaError("parameter_values must be a dict")
    
    # Check enum for topology_class if present
    topology_class = record.get("topology_class")
    if topology_class and topology_class not in ["erdos_renyi", "watts_strogatz", "barabasi_albert"]:
        logger.warning(f"Unknown topology_class: {topology_class}. Allowed: erdos_renyi, watts_strogatz, barabasi_albert")

    return True

def validate_results_file(records: List[Dict[str, Any]]) -> bool:
    """
    Validates a list of records against the results schema.
    """
    for i, record in enumerate(records):
        try:
            validate_simulation_run(record)
        except SchemaError as e:
            raise SchemaError(f"Validation failed for record {i}: {e}")
    return True

def save_results(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Validates and saves the simulation results to a JSON file.
    Ensures the output directory exists.
    """
    if not records:
        logger.warning("No results to save.")
        return

    try:
        validate_results_file(records)
    except SchemaError as e:
        raise SchemaError(f"Cannot save invalid results: {e}")

    path = Path(output_path)
    ensure_data_directory(path)

    with open(path, 'w') as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"Saved {len(records)} simulation results to {output_path}")

def load_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Loads and validates simulation results from a JSON file.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")

    with open(path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SchemaError("Results file must contain a JSON array")

    validate_results_file(data)
    return data