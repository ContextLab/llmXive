"""
Schema Generator for llmXive Research Pipeline.

This module generates JSON Schema YAML files for data validation artifacts.
It is the implementation artifact for Task T010.

Usage:
    python code/utils/schema_generator.py
    
This will generate:
    - contracts/diffusion_results.schema.yaml
    - contracts/bootstrap_stats.schema.yaml
    - contracts/sensitivity_report.schema.yaml
"""
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Ensure the contracts directory exists
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_diffusion_results_schema() -> Dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Diffusion Results",
        "description": "Schema for storing diffusion coefficient results extracted from MD simulations.",
        "type": "object",
        "required": [
            "experiment_id", "solvent", "timescale_ns", "force_field",
            "msd_r_squared", "diffusion_coefficient", "scaled_diffusion_coefficient",
            "nist_reference", "mae", "timestamp"
        ],
        "properties": {
            "experiment_id": {
                "type": "string",
                "description": "Unique identifier for the simulation run"
            },
            "solvent": {
                "type": "string",
                "enum": ["water", "ethanol", "acetone"],
                "description": "Solvent type simulated"
            },
            "timescale_ns": {
                "type": "number",
                "minimum": 0,
                "description": "Simulation duration in nanoseconds"
            },
            "force_field": {
                "type": "string",
                "description": "Force field used (e.g., MARTINI)"
            },
            "msd_r_squared": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "R-squared value from linear regression of MSD vs time"
            },
            "diffusion_coefficient": {
                "type": "number",
                "description": "Raw diffusion coefficient calculated from MSD slope (Å²/ns)"
            },
            "scaled_diffusion_coefficient": {
                "type": "number",
                "description": "Diffusion coefficient after applying solvent-specific scaling factor"
            },
            "nist_reference": {
                "type": "number",
                "description": "Experimental diffusion coefficient from NIST (Å²/ns)"
            },
            "mae": {
                "type": "number",
                "description": "Mean Absolute Error between scaled simulation and NIST reference"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp of when the result was generated"
            },
            "simulation_path": {
                "type": "string",
                "description": "Relative path to the simulation output files"
            },
            "log_path": {
                "type": "string",
                "description": "Relative path to the simulation log file"
            }
        },
        "additionalProperties": False
    }

def generate_bootstrap_stats_schema() -> Dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Bootstrap Statistics",
        "description": "Schema for bootstrap resampling statistics on Mean Absolute Error (MAE).",
        "type": "object",
        "required": [
            "experiment_id", "solvent", "timescale_ns", "bootstrap_iterations",
            "mae_mean", "mae_ci_lower", "mae_ci_upper", "ci_level", "timestamp"
        ],
        "properties": {
            "experiment_id": {
                "type": "string",
                "description": "Unique identifier linking to the diffusion results"
            },
            "solvent": {
                "type": "string",
                "enum": ["water", "ethanol", "acetone"],
                "description": "Solvent type"
            },
            "timescale_ns": {
                "type": "number",
                "minimum": 0,
                "description": "Simulation duration in nanoseconds"
            },
            "bootstrap_iterations": {
                "type": "integer",
                "minimum": 1,
                "description": "Number of bootstrap iterations performed"
            },
            "mae_mean": {
                "type": "number",
                "description": "Mean of the bootstrap MAE distribution"
            },
            "mae_ci_lower": {
                "type": "number",
                "description": "Lower bound of the confidence interval (percentile method)"
            },
            "mae_ci_upper": {
                "type": "number",
                "description": "Upper bound of the confidence interval (percentile method)"
            },
            "ci_level": {
                "type": "number",
                "description": "Confidence level (e.g., 0.95 for 95% CI)"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp of generation"
            },
            "fallback_triggered": {
                "type": "boolean",
                "description": "True if the iteration count was reduced due to wall-clock time limits"
            }
        },
        "additionalProperties": False
    }

def generate_sensitivity_report_schema() -> Dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Sensitivity Report",
        "description": "Schema for sensitivity analysis results across regression start times.",
        "type": "object",
        "required": [
            "experiment_id", "solvent", "timescale_ns", "start_time_percentages",
            "diffusion_coefficients", "variance_percentage", "passes_threshold", "timestamp"
        ],
        "properties": {
            "experiment_id": {
                "type": "string",
                "description": "Unique identifier linking to the diffusion results"
            },
            "solvent": {
                "type": "string",
                "enum": ["water", "ethanol", "acetone"],
                "description": "Solvent type"
            },
            "timescale_ns": {
                "type": "number",
                "minimum": 0,
                "description": "Simulation duration in nanoseconds"
            },
            "start_time_percentages": {
                "type": "array",
                "items": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "description": "List of regression start time percentages (e.g., [0.1, 0.2, 0.3])"
            },
            "diffusion_coefficients": {
                "type": "array",
                "items": {
                    "type": "number"
                },
                "description": "Calculated diffusion coefficients for each start time"
            },
            "variance_percentage": {
                "type": "number",
                "description": "Variance of diffusion coefficients expressed as a percentage of the mean"
            },
            "passes_threshold": {
                "type": "boolean",
                "description": "True if variance_percentage < 5.0"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 timestamp of generation"
            },
            "details": {
                "type": "object",
                "description": "Optional detailed breakdown per start time",
                "additionalProperties": True
            }
        },
        "additionalProperties": False
    }

def write_schema(schema: Dict[str, Any], filename: str) -> None:
    filepath = CONTRACTS_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print(f"Generated: {filepath}")

def main():
    print(f"Generating JSON Schema YAML files in {CONTRACTS_DIR}...")
    
    # Generate Diffusion Results Schema
    write_schema(generate_diffusion_results_schema(), "diffusion_results.schema.yaml")
    
    # Generate Bootstrap Stats Schema
    write_schema(generate_bootstrap_stats_schema(), "bootstrap_stats.schema.yaml")
    
    # Generate Sensitivity Report Schema
    write_schema(generate_sensitivity_report_schema(), "sensitivity_report.schema.yaml")
    
    print("Schema generation complete.")

if __name__ == "__main__":
    main()
