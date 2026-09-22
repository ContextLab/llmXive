import os
from pathlib import Path
import yaml
from typing import Dict, Any

def ensure_directories():
    """
    Creates the required directory structure for the project:
    - data/raw
    - data/processed
    - data/logs
    - contracts
    """
    base_path = Path(__file__).resolve().parent.parent
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "logs",
        base_path / "contracts",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {directory}")

def create_schema_files():
    """
    Creates the required schema files in the contracts/ directory:
    - dataset.schema.yaml
    - output.schema.yaml
    """
    base_path = Path(__file__).resolve().parent.parent
    contracts_dir = base_path / "contracts"

    if not contracts_dir.exists():
        contracts_dir.mkdir(parents=True, exist_ok=True)

    # Define Dataset Schema
    dataset_schema = {
        "title": "HCP Dataset Schema",
        "description": "Schema for raw and preprocessed HCP data inputs",
        "type": "object",
        "properties": {
            "subject_id": {
                "type": "string",
                "description": "Unique identifier for the subject (e.g., HCP ID)"
            },
            "modality": {
                "type": "string",
                "enum": ["fMRI", "dMRI"],
                "description": "Imaging modality"
            },
            "file_path": {
                "type": "string",
                "description": "Absolute or relative path to the data file"
            },
            "acquisition_params": {
                "type": "object",
                "properties": {
                    "TR": {"type": "number", "description": "Repetition time in seconds"},
                    "TE": {"type": "number", "description": "Echo time in seconds"},
                    "voxel_size": {"type": "array", "items": {"type": "number"}}
                }
            }
        },
        "required": ["subject_id", "modality", "file_path"]
    }

    # Define Output Schema
    output_schema = {
        "title": "Pipeline Output Schema",
        "description": "Schema for aggregated metrics and correlation results",
        "type": "object",
        "properties": {
            "structural_metrics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"},
                        "global_efficiency": {"type": "number"},
                        "average_clustering": {"type": "number"},
                        "modularity": {"type": "number"},
                        "density": {"type": "number"}
                    },
                    "required": ["subject_id", "global_efficiency", "average_clustering", "modularity"]
                }
            },
            "dynamic_metrics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"},
                        "state_id": {"type": "integer"},
                        "mean_dwell_time": {"type": "number"},
                        "num_visits": {"type": "integer"}
                    },
                    "required": ["subject_id", "state_id", "mean_dwell_time", "num_visits"]
                }
            },
            "correlation_results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "metric_pair": {"type": "string"},
                        "r_value": {"type": "number"},
                        "p_value": {"type": "number"},
                        "fdr_corrected_p": {"type": "number"},
                        "is_significant": {"type": "boolean"}
                    },
                    "required": ["metric_pair", "r_value", "p_value", "fdr_corrected_p", "is_significant"]
                }
            },
            "exclusion_log": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject_id": {"type": "string"},
                        "reason": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"}
                    }
                }
            }
        },
        "required": ["structural_metrics", "dynamic_metrics", "correlation_results"]
    }

    # Write Dataset Schema
    dataset_path = contracts_dir / "dataset.schema.yaml"
    with open(dataset_path, "w") as f:
        yaml.dump(dataset_schema, f, default_flow_style=False, sort_keys=False)
    print(f"Created schema: {dataset_path}")

    # Write Output Schema
    output_path = contracts_dir / "output.schema.yaml"
    with open(output_path, "w") as f:
        yaml.dump(output_schema, f, default_flow_style=False, sort_keys=False)
    print(f"Created schema: {output_path}")

def main():
    """
    Main entry point to setup data directories and schema files.
    """
    print("Starting data structure setup...")
    ensure_directories()
    create_schema_files()
    print("Data structure setup complete.")

if __name__ == "__main__":
    main()
