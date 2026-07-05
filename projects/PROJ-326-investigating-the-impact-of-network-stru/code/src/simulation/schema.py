"""
Schema definitions and validation for simulation results.

This module defines the JSON schema for SimulationRun entities and provides
functions to validate, save, and load simulation results.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# JSON Schema for SimulationRun entity
SIMULATION_RUN_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "network_id",
        "seed",
        "diffusion_rate",
        "topology_class",
        "timestamp"
    ],
    "properties": {
        "network_id": {
            "type": "string",
            "description": "Unique identifier for the network graph"
        },
        "seed": {
            "type": "integer",
            "description": "Random seed used for the simulation"
        },
        "diffusion_rate": {
            "type": "number",
            "description": "Calculated rate of change of spatial variance"
        },
        "topology_class": {
            "type": "string",
            "enum": ["erdos_renyi", "watts_strogatz", "barabasi_albert"],
            "description": "Class of network topology used"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the simulation run"
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
        },
        "simulation_steps": {
            "type": "integer",
            "description": "Number of time steps simulated"
        },
        "final_energy_density": {
            "type": "number",
            "description": "Energy density at the final time step"
        },
        "spatial_variance_final": {
            "type": "number",
            "description": "Spatial variance at the final time step"
        }
    }
}

# Results file schema (list of SimulationRun objects)
RESULTS_FILE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["results", "metadata"],
    "properties": {
        "results": {
            "type": "array",
            "items": SIMULATION_RUN_SCHEMA,
            "description": "List of simulation run results"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "description": "Schema version"
                },
                "generated_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Timestamp when the file was generated"
                },
                "total_runs": {
                    "type": "integer",
                    "description": "Total number of simulation runs"
                }
            },
            "required": ["version", "generated_at", "total_runs"]
        }
    }
}


def get_schema() -> Dict[str, Any]:
    """
    Returns the JSON schema for a single SimulationRun entity.
    
    Returns:
        Dict containing the JSON schema definition.
    """
    return SIMULATION_RUN_SCHEMA


def get_results_schema() -> Dict[str, Any]:
    """
    Returns the JSON schema for the results file (containing multiple runs).
    
    Returns:
        Dict containing the results file JSON schema definition.
    """
    return RESULTS_FILE_SCHEMA


def validate_simulation_run(run_data: Dict[str, Any]) -> bool:
    """
    Validates a single simulation run dictionary against the schema.
    
    Args:
        run_data: Dictionary containing simulation run data.
        
    Returns:
        True if valid, raises ValueError if invalid.
        
    Raises:
        ValueError: If required fields are missing or types are incorrect.
    """
    schema = get_schema()
    
    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in run_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Type validation
    properties = schema.get("properties", {})
    for field, value in run_data.items():
        if field in properties:
            expected_type = properties[field].get("type")
            
            if expected_type == "string" and not isinstance(value, str):
                raise ValueError(f"Field '{field}' must be a string, got {type(value).__name__}")
            elif expected_type == "integer" and not isinstance(value, int):
                raise ValueError(f"Field '{field}' must be an integer, got {type(value).__name__}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"Field '{field}' must be a number, got {type(value).__name__}")
            
            # Enum validation
            if "enum" in properties[field]:
                if value not in properties[field]["enum"]:
                    raise ValueError(f"Field '{field}' must be one of {properties[field]['enum']}, got {value}")
    
    return True


def validate_results_file(data: Dict[str, Any]) -> bool:
    """
    Validates a complete results file dictionary against the schema.
    
    Args:
        data: Dictionary containing the results file structure.
        
    Returns:
        True if valid, raises ValueError if invalid.
        
    Raises:
        ValueError: If structure is invalid or individual runs fail validation.
    """
    schema = get_results_schema()
    
    # Check required top-level fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in results file: {field}")
    
    # Validate results array
    results = data.get("results", [])
    if not isinstance(results, list):
        raise ValueError("Field 'results' must be a list")
    
    for i, run in enumerate(results):
        try:
            validate_simulation_run(run)
        except ValueError as e:
            raise ValueError(f"Invalid simulation run at index {i}: {e}")
    
    # Validate metadata
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("Field 'metadata' must be an object")
    
    required_meta = schema["properties"]["metadata"]["required"]
    for field in required_meta:
        if field not in metadata:
            raise ValueError(f"Missing required metadata field: {field}")
    
    return True


def save_results(
    results: List[Dict[str, Any]],
    output_path: str | Path,
    version: str = "1.0.0"
) -> Path:
    """
    Saves a list of simulation results to a JSON file with metadata.
    
    Args:
        results: List of simulation run dictionaries.
        output_path: Path to the output JSON file.
        version: Schema version string.
        
    Returns:
        Path to the saved file.
        
    Raises:
        ValueError: If any result fails schema validation.
        IOError: If file cannot be written.
    """
    from datetime import datetime, timezone
    
    output_path = Path(output_path)
    
    # Validate each result before saving
    for result in results:
        validate_simulation_run(result)
    
    # Build the results file structure
    data = {
        "results": results,
        "metadata": {
            "version": version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_runs": len(results)
        }
    }
    
    # Validate the complete structure
    validate_results_file(data)
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return output_path


def load_results(input_path: str | Path) -> List[Dict[str, Any]]:
    """
    Loads simulation results from a JSON file.
    
    Args:
        input_path: Path to the input JSON file.
        
    Returns:
        List of simulation run dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file content fails schema validation.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Results file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    validate_results_file(data)
    
    return data["results"]