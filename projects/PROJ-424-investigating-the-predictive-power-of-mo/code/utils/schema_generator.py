import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import data models to access their structure/fields if needed, 
# though we will define schemas explicitly to match JSON Schema draft 7/2020-12
# The API surface shows these exist:
# from data_models.diffusion_results import DiffusionResults
# from data_models.bootstrap_stats import BootstrapStats
# from data_models.sensitivity_report import SensitivityReport

def generate_diffusion_results_schema() -> Dict[str, Any]:
    """Generate JSON Schema for diffusion_results artifacts."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "diffusion_results.schema.yaml",
        "title": "Diffusion Results",
        "description": "Schema for diffusion coefficient calculation results from MD simulations.",
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "Unique identifier for the simulation run."
            },
            "solvent": {
                "type": "string",
                "enum": ["water", "ethanol", "acetone"],
                "description": "The solvent type simulated."
            },
            "timescale_ns": {
                "type": "number",
                "description": "Simulation duration in nanoseconds."
            },
            "msd_r_squared": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "R-squared value of the linear regression on MSD."
            },
            "diffusion_coefficient": {
                "type": "number",
                "description": "Calculated diffusion coefficient (e.g., in nm^2/ns)."
            },
            "scaled_diffusion_coefficient": {
                "type": "number",
                "description": "Diffusion coefficient after applying solvent-specific scaling factor."
            },
            "nist_reference": {
                "type": "number",
                "description": "Experimental reference value from NIST."
            },
            "absolute_error": {
                "type": "number",
                "description": "Absolute error between scaled coefficient and NIST reference."
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp of the analysis."
            },
            "status": {
                "type": "string",
                "enum": ["success", "failed", "warning"],
                "description": "Status of the analysis."
            },
            "error_message": {
                "type": ["string", "null"],
                "description": "Error message if status is failed or warning."
            }
        },
        "required": ["run_id", "solvent", "timescale_ns", "diffusion_coefficient", "timestamp", "status"]
    }

def generate_bootstrap_stats_schema() -> Dict[str, Any]:
    """Generate JSON Schema for bootstrap_stats artifacts."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "bootstrap_stats.schema.yaml",
        "title": "Bootstrap Statistics",
        "description": "Schema for bootstrap resampling statistics on MAE distributions.",
        "type": "object",
        "properties": {
            "experiment_id": {
                "type": "string",
                "description": "Identifier for the batch experiment."
            },
            "iterations": {
                "type": "integer",
                "minimum": 1,
                "description": "Number of bootstrap iterations performed."
            },
            "mean_mae": {
                "type": "number",
                "description": "Mean Absolute Error across all bootstrap samples."
            },
            "ci_lower_95": {
                "type": "number",
                "description": "Lower bound of the 95% confidence interval."
            },
            "ci_upper_95": {
                "type": "number",
                "description": "Upper bound of the 95% confidence interval."
            },
            "solvent_breakdown": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "solvent": {"type": "string"},
                        "timescale_ns": {"type": "number"},
                        "mean_mae": {"type": "number"},
                        "ci_lower": {"type": "number"},
                        "ci_upper": {"type": "number"}
                    },
                    "required": ["solvent", "timescale_ns", "mean_mae", "ci_lower", "ci_upper"]
                },
                "description": "Detailed stats per solvent-timescale combination."
            },
            "generated_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp of generation."
            }
        },
        "required": ["experiment_id", "iterations", "mean_mae", "ci_lower_95", "ci_upper_95", "generated_at"]
    }

def generate_sensitivity_report_schema() -> Dict[str, Any]:
    """Generate JSON Schema for sensitivity_report artifacts."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "sensitivity_report.schema.yaml",
        "title": "Sensitivity Report",
        "description": "Schema for sensitivity analysis results regarding regression start times.",
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "Identifier for the run being analyzed."
            },
            "total_trajectory_length_ns": {
                "type": "number",
                "description": "Total length of the trajectory in ns."
            },
            "variance_threshold": {
                "type": "number",
                "description": "Maximum allowed variance percentage (e.g., 5.0)."
            },
            "is_stable": {
                "type": "boolean",
                "description": "True if variance in D values is below threshold."
            },
            "sensitivity_points": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start_time_fraction": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Fraction of trajectory used as start time."
                        },
                        "diffusion_coefficient": {
                            "type": "number",
                            "description": "Calculated D for this start time."
                        },
                        "msd_r_squared": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["start_time_fraction", "diffusion_coefficient", "msd_r_squared"]
                },
                "description": "List of results for each sweep point."
            },
            "generated_at": {
                "type": "string",
                "format": "date-time"
            }
        },
        "required": ["run_id", "total_trajectory_length_ns", "is_stable", "sensitivity_points", "generated_at"]
    }

def write_schema(schema: Dict[str, Any], filename: str, output_dir: Path) -> None:
    """Write a schema dictionary to a YAML file."""
    output_path = output_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"Schema written to: {output_path}")

def main() -> None:
    """Main entry point to generate all contract schemas."""
    # Determine output directory based on project structure
    # Assuming this script runs from the project root or code/ directory
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    contracts_dir = project_root / "contracts"
    
    # Ensure contracts directory exists
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    schemas = [
        (generate_diffusion_results_schema(), "diffusion_results.schema.yaml"),
        (generate_bootstrap_stats_schema(), "bootstrap_stats.schema.yaml"),
        (generate_sensitivity_report_schema(), "sensitivity_report.schema.yaml")
    ]
    
    for schema, filename in schemas:
        write_schema(schema, filename, contracts_dir)
    
    print("All schemas generated successfully.")

if __name__ == "__main__":
    main()
