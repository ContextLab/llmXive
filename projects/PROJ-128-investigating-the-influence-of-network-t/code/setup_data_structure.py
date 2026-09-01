"""
Setup script to create the project directory structure and initialize schema files.
This script ensures that all required directories (code/, data/, contracts/, tests/)
exist and creates placeholder schema files in the contracts/ directory.
"""

import os
from pathlib import Path
import yaml
from typing import Dict, Any


def ensure_directories():
    """
    Create the required project directory structure.
    """
    base_dirs = [
        "code",
        "code/preprocess",
        "code/analysis",
        "code/reports",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/figures",
        "data/logs",
        "contracts",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    for dir_path in base_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

    # Create __init__.py files to make directories proper Python packages
    package_dirs = [
        "code",
        "code/preprocess",
        "code/analysis",
        "code/reports",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    for dir_path in package_dirs:
        init_file = Path(dir_path) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")


def create_schema_files():
    """
    Create placeholder schema files in the contracts/ directory.
    """
    contracts_dir = Path("contracts")

    # Dataset schema
    dataset_schema = {
        "name": "HCP Brain Connectivity Dataset",
        "version": "1.0.0",
        "description": "Schema for HCP diffusion and functional MRI data",
        "fields": {
            "subject_id": {
                "type": "string",
                "description": "Unique subject identifier"
            },
            "age": {
                "type": "integer",
                "description": "Subject age in years"
            },
            "sex": {
                "type": "string",
                "enum": ["M", "F"],
                "description": "Subject sex"
            },
            "dwi_path": {
                "type": "string",
                "description": "Path to diffusion MRI data"
            },
            "func_path": {
                "type": "string",
                "description": "Path to functional MRI data"
            },
            "aparc_path": {
                "type": "string",
                "description": "Path to anatomical parcellation"
            }
        },
        "required": ["subject_id", "dwi_path", "func_path", "aparc_path"]
    }

    dataset_schema_file = contracts_dir / "dataset.schema.yaml"
    with open(dataset_schema_file, 'w') as f:
        yaml.dump(dataset_schema, f, default_flow_style=False)
    print(f"Created schema: {dataset_schema_file}")

    # Output schema
    output_schema = {
        "name": "Brain Connectivity Analysis Output",
        "version": "1.0.0",
        "description": "Schema for analysis output files",
        "files": {
            "structural_metrics.csv": {
                "description": "Per-subject structural graph metrics",
                "columns": ["subject_id", "global_efficiency", "clustering_coeff", "modularity", "sparsity"]
            },
            "dynamic_metrics.csv": {
                "description": "Per-subject dynamic functional metrics",
                "columns": ["subject_id", "dwell_time", "visited_states", "transition_matrix"]
            },
            "correlation_results.csv": {
                "description": "Structure-function correlation results",
                "columns": ["metric_pair", "correlation", "p_value", "fdr_corrected_p", "significant"]
            },
            "sensitivity_comparison.csv": {
                "description": "Sensitivity analysis results",
                "columns": ["metric_pair", "baseline_corr", "sensitivity_corr", "absolute_diff"]
            },
            "final_report.json": {
                "description": "Final analysis report",
                "type": "object"
            },
            "exclusion_log.json": {
                "description": "Log of excluded subjects",
                "type": "array"
            }
        }
    }

    output_schema_file = contracts_dir / "output.schema.yaml"
    with open(output_schema_file, 'w') as f:
        yaml.dump(output_schema, f, default_flow_style=False)
    print(f"Created schema: {output_schema_file}")


def main():
    """
    Main entry point for the setup script.
    """
    print("=" * 60)
    print("Setting up project directory structure...")
    print("=" * 60)

    ensure_directories()
    create_schema_files()

    print("=" * 60)
    print("Setup complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()