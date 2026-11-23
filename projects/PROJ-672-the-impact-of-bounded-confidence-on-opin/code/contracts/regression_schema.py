"""
Regression Schema Definitions for Bounded Confidence Analysis.

This module defines the data structures and JSON schemas required for the
regression analysis phase (User Story 3). It establishes the contract for
mapping structural network metrics to simulation IDs and eventual scaling exponents.

Per FR-006 and T016a requirements:
- Defines the schema for `regression_data.json`.
- Maps structural metrics (assortativity, path length, etc.) to simulation IDs.
- Does NOT populate with gamma values yet (that is T016b/US3 dependency).
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from pathlib import Path


@dataclass
class RegressionRecord:
    """
    A single record mapping structural metrics to a specific simulation run.

    Attributes:
        simulation_id (str): Unique identifier for the simulation run (e.g., from manifest).
        topology_type (str): One of 'erdos_renyi', 'barabasi_albert', 'watts_strogatz'.
        network_size (int): Number of nodes N in the network.
        assortativity (float): Pearson correlation coefficient of degrees.
        average_path_length (float): Average shortest path length.
        clustering_coefficient (float): Global clustering coefficient.
        density (float): Ratio of actual edges to possible edges.
        is_connected (bool): Whether the network is fully connected.
        # Note: 'gamma' and 'epsilon_c' fields are intentionally omitted here.
        # They will be added in T016b after simulation analysis (US3) is complete.
    """
    simulation_id: str
    topology_type: str
    network_size: int
    assortativity: float
    average_path_length: float
    clustering_coefficient: float
    density: float
    is_connected: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass instance to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegressionRecord':
        """Create a RegressionRecord instance from a dictionary."""
        return cls(**data)


def get_regression_schema() -> Dict[str, Any]:
    """
    Returns the JSON Schema definition for the regression_data.json file.

    This schema validates the structure of the dataset before analysis.
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Regression Analysis Data Schema",
        "description": "Schema for mapping structural network metrics to simulation IDs.",
        "type": "object",
        "properties": {
            "metadata": {
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "generated_at": {"type": "string", "format": "date-time"},
                    "source": {"type": "string", "description": "Source of the metrics (e.g., T013)"},
                    "missing_gamma": {
                        "type": "boolean",
                        "const": True,
                        "description": "Flag indicating gamma values are not yet populated (T016a state)."
                    }
                },
                "required": ["version", "missing_gamma"]
            },
            "records": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "simulation_id": {"type": "string"},
                        "topology_type": {
                            "type": "string",
                            "enum": ["erdos_renyi", "barabasi_albert", "watts_strogatz"]
                        },
                        "network_size": {"type": "integer", "minimum": 1},
                        "assortativity": {"type": "number"},
                        "average_path_length": {"type": "number"},
                        "clustering_coefficient": {"type": "number"},
                        "density": {"type": "number"},
                        "is_connected": {"type": "boolean"}
                    },
                    "required": [
                        "simulation_id", "topology_type", "network_size",
                        "assortativity", "average_path_length",
                        "clustering_coefficient", "density", "is_connected"
                    ]
                }
            }
        },
        "required": ["metadata", "records"]
    }


def validate_record(record: Dict[str, Any]) -> bool:
    """
    Basic validation of a regression record against expected types.

    This is a lightweight runtime check; full validation should use jsonschema.
    """
    required_fields = [
        "simulation_id", "topology_type", "network_size",
        "assortativity", "average_path_length",
        "clustering_coefficient", "density", "is_connected"
    ]
    if not all(field in record for field in required_fields):
        return False
    if record["topology_type"] not in ["erdos_renyi", "barabasi_albert", "watts_strogatz"]:
        return False
    return True


def create_empty_regression_dataset() -> Dict[str, Any]:
    """
    Creates an empty dataset structure ready for population in T016b.
    """
    return {
        "metadata": {
            "version": "1.0.0",
            "generated_at": None,  # To be filled by caller if needed
            "source": "T013_metrics_extraction",
            "missing_gamma": True
        },
        "records": []
    }


def save_regression_schema_to_file(output_path: str) -> None:
    """
    Saves the JSON schema definition to a file for external validation tools.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = get_regression_schema()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)


def main():
    """
    CLI entry point to generate the schema file and an empty dataset template.
    """
    import datetime

    schema_path = "code/contracts/regression_schema.json"
    dataset_template_path = "data/processed/regression_data_template.json"

    print(f"Generating schema at: {schema_path}")
    save_regression_schema_to_file(schema_path)

    print(f"Generating empty dataset template at: {dataset_template_path}")
    dataset = create_empty_regression_dataset()
    dataset["metadata"]["generated_at"] = datetime.datetime.now().isoformat()
    
    Path(dataset_template_path).parent.mkdir(parents=True, exist_ok=True)
    with open(dataset_template_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2)

    print("Done. The schema is ready. T016b will populate 'records' with gamma values.")


if __name__ == "__main__":
    main()
