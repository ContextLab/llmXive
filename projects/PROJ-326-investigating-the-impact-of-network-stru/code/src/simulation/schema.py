import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class SchemaError(Exception):
    """Custom exception for schema validation errors."""
    pass

def get_schema() -> Dict[str, Any]:
    """
    Returns the JSON Schema definition for the SimulationRun entity.
    This schema is defined in T029a.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
            "network_id",
            "seed",
            "diffusion_rate",
            "topology_class",
            "steps_run",
            "status",
            "runtime_duration_seconds",
            "generation_algorithm",
            "parameter_values"
        ],
        "properties": {
            "network_id": {
                "type": "string",
                "description": "Unique identifier for the network graph."
            },
            "seed": {
                "type": "integer",
                "description": "Random seed used for simulation."
            },
            "diffusion_rate": {
                "type": "number",
                "description": "Calculated rate of energy diffusion."
            },
            "topology_class": {
                "type": "string",
                "enum": ["ErdosRenyi", "WattsStrogatz", "BarabasiAlbert"],
                "description": "The topology class of the generated network."
            },
            "steps_run": {
                "type": "integer",
                "description": "Number of simulation steps executed."
            },
            "status": {
                "type": "string",
                "description": "Status of the simulation run (e.g., 'SUCCESS', '[SIMULATION_DIVERGENCE]')."
            },
            "runtime_duration_seconds": {
                "type": "number",
                "description": "Wall-clock execution time in seconds."
            },
            "generation_algorithm": {
                "type": "string",
                "description": "Name of the algorithm used to generate the graph."
            },
            "parameter_values": {
                "type": "object",
                "description": "Dictionary of parameters used for graph generation."
            }
        },
        "additionalProperties": False
    }

def get_results_schema() -> Dict[str, Any]:
    """
    Returns the schema for a list of simulation results.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array",
        "items": get_schema()
    }

def validate_simulation_run(data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> None:
    """
    Validates a single simulation result against the schema.
    
    Raises:
        SchemaError: If validation fails.
    """
    if schema is None:
        schema = get_schema()
    
    # Manual validation to avoid external dependency if jsonschema is not installed
    # but the project requirements include it. Using jsonschema is safer.
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        # Fallback manual validation if jsonschema is missing (though requirements.txt should have it)
        logger.warning("jsonschema library not found. Performing manual validation.")
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                raise SchemaError(f"Missing required field: {field}")
        
        # Type checking for critical fields
        if not isinstance(data.get("network_id"), str):
            raise SchemaError("network_id must be a string")
        if not isinstance(data.get("seed"), int):
            raise SchemaError("seed must be an integer")
        if not isinstance(data.get("diffusion_rate"), (int, float)):
            raise SchemaError("diffusion_rate must be a number")
        if not isinstance(data.get("topology_class"), str):
            raise SchemaError("topology_class must be a string")
        if not isinstance(data.get("steps_run"), int):
            raise SchemaError("steps_run must be an integer")
        if not isinstance(data.get("status"), str):
            raise SchemaError("status must be a string")
        if not isinstance(data.get("runtime_duration_seconds"), (int, float)):
            raise SchemaError("runtime_duration_seconds must be a number")
        if not isinstance(data.get("generation_algorithm"), str):
            raise SchemaError("generation_algorithm must be a string")
        if not isinstance(data.get("parameter_values"), dict):
            raise SchemaError("parameter_values must be an object")
        
        # Check enum for topology_class
        allowed_classes = ["ErdosRenyi", "WattsStrogatz", "BarabasiAlbert"]
        if data.get("topology_class") not in allowed_classes:
            raise SchemaError(f"topology_class must be one of {allowed_classes}")
            
    except jsonschema.ValidationError as e:
        raise SchemaError(f"Schema validation failed: {e.message}")
    except jsonschema.SchemaError as e:
        raise SchemaError(f"Invalid schema definition: {e.message}")

def validate_results_file(file_path: Path) -> bool:
    """
    Validates a JSON file containing a list of simulation results.
    
    Returns:
        True if valid, raises SchemaError if invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise SchemaError(f"Invalid JSON format: {e}")
    
    if not isinstance(data, list):
        raise SchemaError("Root element must be a list of results.")
    
    schema = get_results_schema()
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
    except ImportError:
        # Manual validation for list
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise SchemaError(f"Item {i} is not an object.")
            validate_simulation_run(item)
    except jsonschema.ValidationError as e:
        raise SchemaError(f"Schema validation failed for item {e.instance_path}: {e.message}")
    
    return True

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves a list of results to a JSON file after validating them.
    """
    # Validate first
    schema = get_results_schema()
    for i, result in enumerate(results):
        try:
            validate_simulation_run(result, schema)
        except SchemaError as e:
            raise SchemaError(f"Result at index {i} failed validation: {e}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved {len(results)} results to {output_path}")

def load_results(file_path: Path) -> List[Dict[str, Any]]:
    """
    Loads and validates results from a JSON file.
    """
    validate_results_file(file_path)
    with open(file_path, 'r') as f:
        return json.load(f)