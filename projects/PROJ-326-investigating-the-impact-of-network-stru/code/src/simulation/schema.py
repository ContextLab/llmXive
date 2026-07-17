import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from code.src.utils.reproducibility import ensure_data_directory
from datetime import datetime

class SchemaError(Exception):
    """Raised when schema validation fails."""
    pass

# Define the SimulationRun entity schema
SIMULATION_RUN_SCHEMA = {
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
            "description": "Class of topology (e.g., ErdosRenyi, WattsStrogatz, BarabasiAlbert)"
        },
        "steps_run": {
            "type": "integer",
            "description": "Number of simulation steps executed"
        },
        "status": {
            "type": "string",
            "enum": ["completed", "failed", "timeout", "diverged"],
            "description": "Final status of the simulation run"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the run"
        },
        "energy_density_profile": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Optional: energy density at each step",
            "optional": True
        },
        "spatial_variance_history": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Optional: spatial variance at each step",
            "optional": True
        }
    }
}

def get_schema() -> Dict[str, Any]:
    """Return the full schema for a simulation run result."""
    return SIMULATION_RUN_SCHEMA

def get_results_schema() -> Dict[str, Any]:
    """Alias for get_schema, returns the schema for simulation results."""
    return SIMULATION_RUN_SCHEMA

def validate_simulation_run(data: Dict[str, Any]) -> bool:
    """
    Validate that the provided data dictionary matches the SimulationRun schema.
    Raises SchemaError if validation fails.
    """
    required_fields = SIMULATION_RUN_SCHEMA["required"]
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise SchemaError(f"Missing required fields: {missing_fields}")
    
    # Type checking for required fields
    if not isinstance(data["network_id"], str):
        raise SchemaError(f"Field 'network_id' must be a string, got {type(data['network_id'])}")
    
    if not isinstance(data["seed"], int):
        raise SchemaError(f"Field 'seed' must be an integer, got {type(data['seed'])}")
    
    if not isinstance(data["diffusion_rate"], (int, float)):
        raise SchemaError(f"Field 'diffusion_rate' must be a number, got {type(data['diffusion_rate'])}")
    
    if not isinstance(data["topology_class"], str):
        raise SchemaError(f"Field 'topology_class' must be a string, got {type(data['topology_class'])}")
    
    if not isinstance(data["steps_run"], int):
        raise SchemaError(f"Field 'steps_run' must be an integer, got {type(data['steps_run'])}")
    
    if not isinstance(data["status"], str):
        raise SchemaError(f"Field 'status' must be a string, got {type(data['status'])}")
    
    if data["status"] not in SIMULATION_RUN_SCHEMA["properties"]["status"]["enum"]:
        raise SchemaError(f"Field 'status' must be one of {SIMULATION_RUN_SCHEMA['properties']['status']['enum']}, got '{data['status']}'")
    
    # Optional fields type checking
    if "timestamp" in data and not isinstance(data["timestamp"], str):
        raise SchemaError(f"Field 'timestamp' must be a string, got {type(data['timestamp'])}")
    
    if "energy_density_profile" in data:
        if not isinstance(data["energy_density_profile"], list):
            raise SchemaError(f"Field 'energy_density_profile' must be a list, got {type(data['energy_density_profile'])}")
        if not all(isinstance(x, (int, float)) for x in data["energy_density_profile"]):
            raise SchemaError(f"Field 'energy_density_profile' must contain only numbers")
    
    if "spatial_variance_history" in data:
        if not isinstance(data["spatial_variance_history"], list):
            raise SchemaError(f"Field 'spatial_variance_history' must be a list, got {type(data['spatial_variance_history'])}")
        if not all(isinstance(x, (int, float)) for x in data["spatial_variance_history"]):
            raise SchemaError(f"Field 'spatial_variance_history' must contain only numbers")
    
    return True

def validate_results_file(file_path: Path) -> bool:
    """
    Load a JSON file and validate it against the SimulationRun schema.
    Raises SchemaError if file is missing, invalid JSON, or schema mismatch.
    """
    if not file_path.exists():
        raise SchemaError(f"Results file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid JSON in {file_path}: {e}")
    
    # Handle case where file contains a list of results or a single result
    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise SchemaError(f"Item {i} in results list is not a dictionary")
            validate_simulation_run(item)
    elif isinstance(data, dict):
        validate_simulation_run(data)
    else:
        raise SchemaError(f"Results file must contain a dictionary or a list of dictionaries")
    
    return True

def save_results(data: Dict[str, Any], output_path: Path) -> None:
    """
    Validate data against schema, ensure directory exists, and save to JSON.
    This is the primary entry point for T029 (serialization).
    """
    # Validate the data first
    validate_simulation_run(data)
    
    # Ensure output directory exists
    ensure_data_directory(output_path)
    
    # Add timestamp if not present
    if "timestamp" not in data:
        data["timestamp"] = datetime.now().isoformat()
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logging.info(f"Simulation results saved and validated: {output_path}")

def load_results(file_path: Path) -> Dict[str, Any]:
    """
    Load and validate results from a JSON file.
    Returns the validated data dictionary.
    """
    validate_results_file(file_path)
    
    with open(file_path, 'r') as f:
        return json.load(f)