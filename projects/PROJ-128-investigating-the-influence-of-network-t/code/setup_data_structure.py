import os
from pathlib import Path
import yaml
from typing import Dict, Any

def ensure_directories():
    """
    Create the required directory structure for the project.
    Creates: data/raw, data/processed, data/logs, contracts
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    contracts_dir = base_dir / "contracts"

    directories = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "logs",
        contracts_dir,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create a .gitkeep file to ensure directories are tracked in git
        (directory / ".gitkeep").touch()

    return True

def create_schema_files():
    """
    Create the required YAML schema files in the contracts directory.
    """
    base_dir = Path(__file__).resolve().parent.parent
    contracts_dir = base_dir / "contracts"

    # Ensure contracts directory exists
    contracts_dir.mkdir(parents=True, exist_ok=True)

    # Define dataset.schema.yaml content
    dataset_schema = {
        "name": "HCP Brain Imaging Dataset",
        "version": "1.0.0",
        "description": "Schema for HCP OpenNeuro dMRI and fMRI data structure",
        "fields": {
            "subject_id": {
                "type": "string",
                "description": "Unique subject identifier (e.g., 100307)",
                "required": True
            },
            "session": {
                "type": "string",
                "description": "Session identifier (e.g., 'MR1')",
                "required": True
            },
            "modality": {
                "type": "string",
                "enum": ["dMRI", "fMRI"],
                "description": "Imaging modality",
                "required": True
            },
            "raw_file_path": {
                "type": "string",
                "description": "Path to the raw NIfTI file",
                "required": True
            },
            "acquisition_params": {
                "type": "object",
                "description": "Acquisition parameters (TR, TE, resolution, etc.)",
                "properties": {
                    "TR": {"type": "float", "description": "Repetition time in seconds"},
                    "TE": {"type": "float", "description": "Echo time in seconds"},
                    "resolution": {"type": "string", "description": "Voxel resolution"}
                },
                "required": True
            }
        }
    }

    # Define output.schema.yaml content
    output_schema = {
        "name": "Pipeline Output Schema",
        "version": "1.0.0",
        "description": "Schema for aggregated metrics and correlation results",
        "files": {
            "structural_metrics.csv": {
                "path": "data/processed/structural_metrics.csv",
                "description": "Aggregated structural graph metrics per subject",
                "columns": {
                    "subject_id": {"type": "string", "required": True},
                    "global_efficiency": {"type": "float", "required": True},
                    "average_clustering": {"type": "float", "required": True},
                    "modularity": {"type": "float", "required": True},
                    "exclusion_reason": {"type": "string", "required": False}
                }
            },
            "dynamic_metrics.csv": {
                "path": "data/processed/dynamic_metrics.csv",
                "description": "Aggregated dynamic functional metrics per subject",
                "columns": {
                    "subject_id": {"type": "string", "required": True},
                    "dwell_time_state_0": {"type": "float", "required": True},
                    "dwell_time_state_1": {"type": "float", "required": True},
                    "dwell_time_state_2": {"type": "float", "required": True},
                    "dwell_time_state_3": {"type": "float", "required": True},
                    "dwell_time_state_4": {"type": "float", "required": True},
                    "visited_states": {"type": "integer", "required": True},
                    "mean_dwell_time": {"type": "float", "required": True}
                }
            },
            "correlation_results.csv": {
                "path": "data/processed/correlation_results.csv",
                "description": "Correlation results between structural and dynamic metrics",
                "columns": {
                    "structural_metric": {"type": "string", "required": True},
                    "dynamic_metric": {"type": "string", "required": True},
                    "correlation_type": {"type": "string", "enum": ["pearson", "spearman"], "required": True},
                    "r_value": {"type": "float", "required": True},
                    "p_value_raw": {"type": "float", "required": True},
                    "p_value_fdr": {"type": "float", "required": True},
                    "is_significant": {"type": "boolean", "required": True}
                }
            },
            "exclusion_log.json": {
                "path": "data/logs/exclusion_log.json",
                "description": "Log of excluded subjects and reasons",
                "structure": {
                    "excluded_subjects": {
                        "type": "array",
                        "items": {
                            "subject_id": "string",
                            "reason": "string",
                            "timestamp": "string"
                        }
                    }
                }
            }
        }
    }

    # Write schema files
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    with open(dataset_schema_path, "w") as f:
        yaml.dump(dataset_schema, f, default_flow_style=False, sort_keys=False)

    output_schema_path = contracts_dir / "output.schema.yaml"
    with open(output_schema_path, "w") as f:
        yaml.dump(output_schema, f, default_flow_style=False, sort_keys=False)

    return True

def main():
    """
    Main entry point for setting up the data structure and schema files.
    """
    print("Setting up project data structure...")
    ensure_directories()
    print("Creating schema files...")
    create_schema_files()
    print("Setup complete.")

if __name__ == "__main__":
    main()
