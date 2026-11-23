"""
JSON Schema definitions for analysis artifacts.

This module defines the strict schema for simulation results and other
analysis artifacts to ensure data integrity and consistency across the pipeline.
"""
import json
from pathlib import Path
from typing import Any, Dict

# Path to the simulation results file
SIMULATION_RESULTS_PATH = Path("data/analysis/simulation_results.json")

# Schema definition for simulation_results.json
SIMULATION_RESULTS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": [
        "run_id",
        "timestamp",
        "runtime_duration_seconds",
        "generation_algorithm",
        "network_params",
        "topology_metrics",
        "simulation_params",
        "diffusion_rate",
        "energy_profile",
        "spatial_variance",
        "stability_status",
        "seed"
    ],
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Unique identifier for this simulation run"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the simulation completion"
        },
        "runtime_duration_seconds": {
            "type": "number",
            "minimum": 0,
            "description": "Total wall-clock time taken for the simulation"
        },
        "generation_algorithm": {
            "type": "string",
            "enum": ["erdos_renyi", "watts_strogatz", "barabasi_albert"],
            "description": "The graph generation algorithm used"
        },
        "network_params": {
            "type": "object",
            "description": "Parameters used for network generation",
            "properties": {
                "n_nodes": {"type": "integer", "minimum": 1},
                "p_edge": {"type": "number", "minimum": 0, "maximum": 1},
                "k_nearest": {"type": "integer", "minimum": 1},
                "beta": {"type": "number", "minimum": 0, "maximum": 1},
                "m_edges": {"type": "integer", "minimum": 1}
            }
        },
        "topology_metrics": {
            "type": "object",
            "description": "Computed topological metrics of the generated graph",
            "properties": {
                "clustering_coefficient": {"type": "number", "minimum": 0, "maximum": 1},
                "average_path_length": {"type": "number", "minimum": 0},
                "diameter": {"type": "integer", "minimum": 0},
                "degree_distribution_stats": {
                    "type": "object",
                    "properties": {
                        "mean": {"type": "number"},
                        "std": {"type": "number"},
                        "min": {"type": "number"},
                        "max": {"type": "number"}
                    }
                }
            }
        },
        "simulation_params": {
            "type": "object",
            "description": "Parameters used for the spin simulation",
            "properties": {
                "temperature": {"type": "number", "minimum": 0},
                "steps": {"type": "integer", "minimum": 1},
                "initial_energy": {"type": "number"},
                "beta_inverse": {"type": "number", "minimum": 0}
            }
        },
        "diffusion_rate": {
            "type": "number",
            "description": "Calculated rate of energy diffusion (change in spatial variance over time)"
        },
        "energy_profile": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Time series of total system energy"
        },
        "spatial_variance": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Time series of spatial variance of energy density"
        },
        "stability_status": {
            "type": "string",
            "enum": ["stable", "divergent", "timeout"],
            "description": "Result of numerical stability checks"
        },
        "seed": {
            "type": "integer",
            "description": "Random seed used for reproducibility"
        }
    }
}

def validate_simulation_results(data: Dict[str, Any]) -> bool:
    """
    Validate a dictionary against the simulation results schema.
    
    Args:
        data: The dictionary to validate.
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        ValueError: If the data is invalid.
    """
    try:
        # Basic type check
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")
        
        # Check required fields
        for field in SIMULATION_RESULTS_SCHEMA["required"]:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Type checking for specific fields
        if not isinstance(data["run_id"], str):
            raise ValueError("run_id must be a string")
        
        if not isinstance(data["timestamp"], str):
            raise ValueError("timestamp must be a string")
        
        if not isinstance(data["runtime_duration_seconds"], (int, float)):
            raise ValueError("runtime_duration_seconds must be a number")
        
        if data["runtime_duration_seconds"] < 0:
            raise ValueError("runtime_duration_seconds must be non-negative")
        
        if data["generation_algorithm"] not in ["erdos_renyi", "watts_strogatz", "barabasi_albert"]:
            raise ValueError("generation_algorithm must be one of: erdos_renyi, watts_strogatz, barabasi_albert")
        
        if not isinstance(data["diffusion_rate"], (int, float)):
            raise ValueError("diffusion_rate must be a number")
        
        if not isinstance(data["energy_profile"], list):
            raise ValueError("energy_profile must be a list")
        
        if not isinstance(data["spatial_variance"], list):
            raise ValueError("spatial_variance must be a list")
        
        if data["stability_status"] not in ["stable", "divergent", "timeout"]:
            raise ValueError("stability_status must be one of: stable, divergent, timeout")
        
        if not isinstance(data["seed"], int):
            raise ValueError("seed must be an integer")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Schema validation failed: {str(e)}")

def save_schema_definition(output_path: Path = None) -> None:
    """
    Save the schema definition to a JSON file for reference.
    
    Args:
        output_path: Optional path to save the schema. Defaults to schema definition file.
    """
    if output_path is None:
        output_path = Path("data/analysis/simulation_results_schema.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(SIMULATION_RESULTS_SCHEMA, f, indent=2)

def main() -> None:
    """
    Main entry point for schema validation and generation.
    
    This function:
    1. Validates the schema definition itself
    2. Saves the schema to a file for reference
    3. Prints validation status
    """
    print("Validating simulation results schema...")
    
    # Test with a minimal valid example
    test_data = {
        "run_id": "test_run_001",
        "timestamp": "2025-01-15T12:00:00Z",
        "runtime_duration_seconds": 45.5,
        "generation_algorithm": "watts_strogatz",
        "network_params": {
            "n_nodes": 100,
            "k_nearest": 4,
            "beta": 0.1
        },
        "topology_metrics": {
            "clustering_coefficient": 0.5,
            "average_path_length": 3.2
        },
        "simulation_params": {
            "temperature": 1.0,
            "steps": 1000
        },
        "diffusion_rate": 0.05,
        "energy_profile": [10.0, 9.8, 9.5],
        "spatial_variance": [0.1, 0.15, 0.2],
        "stability_status": "stable",
        "seed": 42
    }
    
    try:
        validate_simulation_results(test_data)
        print("✓ Schema validation passed with test data")
    except ValueError as e:
        print(f"✗ Schema validation failed: {e}")
        return
    
    # Save schema definition
    save_schema_definition()
    print(f"✓ Schema definition saved to data/analysis/simulation_results_schema.json")
    print("Schema definition complete.")

if __name__ == "__main__":
    main()
