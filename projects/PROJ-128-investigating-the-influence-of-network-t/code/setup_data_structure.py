import os
from pathlib import Path
import yaml
from typing import Dict, Any

def ensure_directories():
    """Create the required directory structure for the project."""
    base = Path(".")
    dirs = [
        "data/raw",
        "data/processed",
        "data/figures",
        "data/logs",
        "contracts",
        "code/preprocess",
        "code/analysis",
        "code/reports",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    return True

def create_schema_files():
    """Create the required schema files in the contracts/ directory."""
    base = Path("contracts")
    
    # Dataset Schema: Defines the structure of the input HCP data
    dataset_schema = {
        "name": "HCP_Dataset_Schema",
        "version": "1.0.0",
        "description": "Schema for HCP OpenNeuro dMRI and fMRI data inputs",
        "entities": {
            "subject": {
                "type": "object",
                "properties": {
                    "subject_id": {"type": "string", "description": "HCP Subject ID"},
                    "age": {"type": "integer"},
                    "sex": {"type": "string", "enum": ["M", "F"]},
                    "handedness": {"type": "string"}
                },
                "required": ["subject_id"]
            },
            "dwi_data": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to .nii.gz file"},
                    "bvals": {"type": "string", "description": "Path to bvals file"},
                    "bvecs": {"type": "string", "description": "Path to bvecs file"},
                    "b0_threshold": {"type": "number"}
                },
                "required": ["file_path", "bvals", "bvecs"]
            },
            "fMRI_data": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to .nii.gz file"},
                    "tr": {"type": "number", "description": " repetition time in seconds"},
                    "task": {"type": "string", "description": "Task name (e.0., 'Rest'}"},
                    "motion_params": {"type": "array", "items": {"type": "number"}}
                },
                "required": ["file_path", "tr"]
            }
        }
    }

    # Output Schema: Defines the structure of the pipeline outputs
    output_schema = {
        "name": "Pipeline_Output_Schema",
        "version": "1.0.0",
        "description": "Schema for structural and dynamic metrics output",
        "files": {
            "structural_metrics.csv": {
                "type": "csv",
                "columns": [
                    {"name": "subject_id", "type": "string"},
                    {"name": "global_efficiency", "type": "number"},
                    {"name": "avg_clustering_coeff", "type": "number"},
                    {"name": "modularity", "type": "number"},
                    {"name": "density", "type": "number"},
                    {"name": "avg_path_length", "type": "number"}
                ]
            },
            "dynamic_metrics.csv": {
                "type": "csv",
                "columns": [
                    {"name": "subject_id", "type": "string"},
                    {"name": "state_id", "type": "integer"},
                    {"name": "mean_d dwell_time", "type": "number"},
                    {"name": "num_visits", "type": "integer"}
                ]
            },
            "correlation_results.csv": {
                "type": "csv",
                "columns": [
                    {"name": "struct_metric", "type": "string"},
                    {"name": "dyn_metric", "type": "string"},
                    {"name": "correlation_r", "type": "number"},
                    {"name": "p_value", "type": "number"},
                    {"name": "fdr_p_value", "type": "number"},
                    {"name": "significant", "type": "boolean"}
                ]
            },
            "exclusion_log.json": {
                "type": "json",
                "structure": {
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
            "completeness_report.json": {
                "type": "json",
                "structure": {
                    "type": "object",
                    "properties": {
                        "total_subjects": {"type": "integer"},
                        "processed_subjects": {"type": "integer"},
                        "excluded_subjects": {"type": "integer"},
                        "completion_percentage": {"type": "number"},
                        "exclusion_breakdown": {"type": "object"}
                    }
                }
            }
        }
    }

    # Write schema files
    with open(base / "dataset.schema.yaml", "w") as f:
        yaml.dump(dataset_schema, f, default_flow_style=False)

    with open(base / "output.schema.yaml", "w") as f:
        yaml.dump(output_schema, f, default_flow_style=False)

    return True

def main():
    """Entry point to setup the data structure and schemas."""
    print("Creating directory structure...")
    ensure_directories()
    print("Directory structure created.")
    
    print("Creating schema files...")
    create_schema_files()
    print("Schema files created.")
    
    print("Setup complete.")

if __name__ == "__main__":
    main()
