"""
Script to initialize the project directory structure and schema files.
This script ensures that all required directories (data/raw, data/processed, data/logs, contracts)
exist and creates the initial schema definition files if they are missing.
"""
import os
from pathlib import Path
import yaml

def ensure_directories():
    """Create the required directory structure."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    contracts_dir = base_dir / "contracts"

    # Define directory structure
    directories = [
        data_dir / "raw" / "fmri",
        data_dir / "raw" / "dmri",
        data_dir / "processed",
        data_dir / "logs",
        contracts_dir,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_schema_files():
    """Create the YAML schema files in the contracts directory."""
    base_dir = Path(__file__).parent.parent
    contracts_dir = base_dir / "contracts"

    # Dataset Schema
    dataset_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "HCP Dataset Schema",
        "description": "Schema for the raw and processed HCP brain imaging dataset structure.",
        "type": "object",
        "properties": {
            "raw": {
                "type": "object",
                "description": "Raw data directories",
                "properties": {
                    "fmri": {"type": "string", "description": "Path to raw fMRI NIfTI files"},
                    "dmri": {"type": "string", "description": "Path to raw dMRI NIfTI files"},
                    "bval": {"type": "string", "description": "Path to dMRI b-values"},
                    "bvec": {"type": "string", "description": "Path to dMRI b-vectors"},
                },
                "required": ["fmri", "dmri"],
            },
            "processed": {
                "type": "object",
                "description": "Processed data artifacts",
                "properties": {
                    "structural_metrics": {
                        "type": "string",
                        "description": "Path to structural metrics CSV",
                    },
                    "dynamic_metrics": {
                        "type": "string",
                        "description": "Path to dynamic metrics CSV",
                    },
                    "correlation_results": {
                        "type": "string",
                        "description": "Path to correlation results CSV",
                    },
                    "sensitivity_results": {
                        "type": "string",
                        "description": "Path to sensitivity analysis results",
                    },
                },
                "required": ["structural_metrics", "dynamic_metrics"],
            },
            "logs": {
                "type": "object",
                "description": "Execution logs",
                "properties": {
                    "exclusion_log": {
                        "type": "string",
                        "description": "Path to subject exclusion log JSON",
                    },
                    "resource_log": {
                        "type": "string",
                        "description": "Path to resource usage log",
                    },
                },
            },
        },
        "required": ["raw", "processed", "logs"],
    }

    # Output Schema
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Pipeline Output Schema",
        "description": "Schema for the final output artifacts of the brain network analysis pipeline.",
        "definitions": {
            "structural_metric": {
                "type": "object",
                "properties": {
                    "subject_id": {"type": "string"},
                    "global_efficiency": {"type": "number", "minimum": 0},
                    "average_clustering": {"type": "number", "minimum": 0},
                    "modularity": {"type": "number"},
                    "density": {"type": "number", "minimum": 0, "maximum": 1},
                    "exclusion_reason": {"type": ["string", "null"]},
                },
                "required": [
                    "subject_id",
                    "global_efficiency",
                    "average_clustering",
                    "modularity",
                    "density",
                ],
            },
            "dynamic_metric": {
                "type": "object",
                "properties": {
                    "subject_id": {"type": "string"},
                    "visited_states": {"type": "integer", "minimum": 0},
                    "mean_dwell_time": {"type": "number", "minimum": 0},
                    "transition_matrix": {"type": "array", "items": {"type": "number"}},
                },
                "required": ["subject_id", "visited_states", "mean_dwell_time"],
            },
            "correlation_result": {
                "type": "object",
                "properties": {
                    "structural_metric": {"type": "string"},
                    "dynamic_metric": {"type": "string"},
                    "correlation_type": {"type": "string", "enum": ["pearson", "spearman"]},
                    "r_value": {"type": "number"},
                    "p_value": {"type": "number", "minimum": 0, "maximum": 1},
                    "fdr_corrected": {"type": "boolean"},
                    "significant": {"type": "boolean"},
                },
                "required": [
                    "structural_metric",
                    "dynamic_metric",
                    "correlation_type",
                    "r_value",
                    "p_value",
                    "fdr_corrected",
                    "significant",
                ],
            },
            "sensitivity_result": {
                "type": "object",
                "properties": {
                    "parameter_name": {"type": "string"},
                    "baseline_value": {"type": "number"},
                    "sensitivity_value": {"type": "number"},
                    "absolute_difference": {"type": "number"},
                    "relative_change_percent": {"type": "number"},
                },
                "required": [
                    "parameter_name",
                    "baseline_value",
                    "sensitivity_value",
                    "absolute_difference",
                    "relative_change_percent",
                ],
            },
        },
        "properties": {
            "structural_metrics_csv": {
                "type": "object",
                "description": "Schema for data/processed/structural_metrics.csv",
                "properties": {
                    "type": {"type": "string", "const": "csv"},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "contains": {
                            "anyOf": [
                                {"const": "subject_id"},
                                {"const": "global_efficiency"},
                                {"const": "average_clustering"},
                                {"const": "modularity"},
                                {"const": "density"},
                            ]
                        },
                    },
                },
            },
            "dynamic_metrics_csv": {
                "type": "object",
                "description": "Schema for data/processed/dynamic_metrics.csv",
                "properties": {
                    "type": {"type": "string", "const": "csv"},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "contains": {
                            "anyOf": [
                                {"const": "subject_id"},
                                {"const": "visited_states"},
                                {"const": "mean_dwell_time"},
                            ]
                        },
                    },
                },
            },
            "correlation_results_csv": {
                "type": "object",
                "description": "Schema for data/processed/correlation_results.csv",
                "properties": {
                    "type": {"type": "string", "const": "csv"},
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "contains": {
                            "anyOf": [
                                {"const": "structural_metric"},
                                {"const": "dynamic_metric"},
                                {"const": "r_value"},
                                {"const": "p_value"},
                                {"const": "fdr_corrected"},
                            ]
                        },
                    },
                },
            },
            "sensitivity_results_json": {
                "type": "object",
                "description": "Schema for data/processed/sensitivity_results.json",
                "properties": {
                    "type": {"type": "string", "const": "json"},
                    "items": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/sensitivity_result"},
                    },
                },
            },
        },
        "required": [
            "structural_metrics_csv",
            "dynamic_metrics_csv",
            "correlation_results_csv",
            "sensitivity_results_json",
        ],
    }

    # Write dataset schema
    dataset_path = contracts_dir / "dataset.schema.yaml"
    with open(dataset_path, "w") as f:
        yaml.dump(dataset_schema, f, default_flow_style=False, sort_keys=False)
    print(f"Created schema file: {dataset_path}")

    # Write output schema
    output_path = contracts_dir / "output.schema.yaml"
    with open(output_path, "w") as f:
        yaml.dump(output_schema, f, default_flow_style=False, sort_keys=False)
    print(f"Created schema file: {output_path}")

def main():
    """Entry point for the setup script."""
    print("Initializing project directory structure...")
    ensure_directories()
    print("Creating schema files...")
    create_schema_files()
    print("Setup complete.")

if __name__ == "__main__":
    main()