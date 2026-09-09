"""
Schema Generator for Data Validation Contracts.

This module generates YAML schema files for the project's data artifacts
(diffusion_results, bootstrap_stats, sensitivity_report) to be used by
the schema validator for data integrity checks.
"""
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Define the schema contents as dictionaries
# These match the content of the .schema.yaml files in contracts/

DIFFUSION_RESULTS_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Diffusion Results",
    "description": (
        "Schema for diffusion coefficient results derived from MD simulations. "
        "Cites Constitution Principle VI and spec.md FR-008 for R² threshold."
    ),
    "type": "object",
    "required": [
        "solvent", "timescale_ns", "msd_slope", "r_squared",
        "diffusion_coefficient", "scaling_factor_applied",
        "linearity_valid", "timestamp"
    ],
    "properties": {
        "solvent": {
            "type": "string",
            "enum": ["water", "ethanol", "acetone"],
            "description": "The solvent simulated."
        },
        "timescale_ns": {
            "type": "number",
            "description": "Simulation duration in nanoseconds."
        },
        "msd_slope": {
            "type": "number",
            "description": "Slope of the Mean Squared Displacement vs. time regression (Å²/ps)."
        },
        "r_squared": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": (
                "R² value of the linear regression. "
                "Must be >= 0.95 per Constitution Principle VI and spec.md FR-008."
            )
        },
        "diffusion_coefficient": {
            "type": "number",
            "description": "Calculated diffusion coefficient in m²/s."
        },
        "scaling_factor_applied": {
            "type": "number",
            "description": "Solvent-specific scaling factor applied to the raw D value."
        },
        "linearity_valid": {
            "type": "boolean",
            "description": "True if R² >= 0.95, False otherwise."
        },
        "trajectory_path": {
            "type": "string",
            "description": "Path to the source trajectory file."
        },
        "regression_start_time_ps": {
            "type": "number",
            "description": "Start time of the linear regression window in ps."
        },
        "regression_end_time_ps": {
            "type": "number",
            "description": "End time of the linear regression window in ps."
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of when the analysis was performed."
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata about the simulation run.",
            "properties": {
                "force_field": {"type": "string"},
                "temperature_k": {"type": "number"},
                "box_size_nm": {
                    "type": "array",
                    "items": {"type": "number"}
                }
            }
        }
    }
}

BOOTSTRAP_STATS_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Bootstrap Statistics",
    "description": (
        "Schema for bootstrap resampling statistics of MAE distributions. "
        "Cites spec.md SC-005 for statistical method (N=3 limitation)."
    ),
    "type": "object",
    "required": [
        "solvent", "timescale_ns", "n_iterations", "mean_mae",
        "std_mae", "ci_lower_95", "ci_upper_95", "timestamp"
    ],
    "properties": {
        "solvent": {
            "type": "string",
            "enum": ["water", "ethanol", "acetone"],
            "description": "The solvent associated with these statistics."
        },
        "timescale_ns": {
            "type": "number",
            "description": "Simulation duration in nanoseconds."
        },
        "n_iterations": {
            "type": "integer",
            "minimum": 1,
            "description": (
                "Number of bootstrap iterations performed. "
                "May be reduced if wall-clock time > 5.5h (per FR-004)."
            )
        },
        "mean_mae": {
            "type": "number",
            "description": "Mean of the Mean Absolute Error distribution."
        },
        "std_mae": {
            "type": "number",
            "description": "Standard deviation of the MAE distribution."
        },
        "ci_lower_95": {
            "type": "number",
            "description": "Lower bound of the 95% confidence interval (percentile method)."
        },
        "ci_upper_95": {
            "type": "number",
            "description": "Upper bound of the 95% confidence interval (percentile method)."
        },
        "mae_distribution_path": {
            "type": "string",
            "description": "Path to the file containing the raw MAE distribution values."
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the analysis."
        },
        "fallback_triggered": {
            "type": "boolean",
            "description": "True if iteration count was reduced due to time budget constraints."
        }
    }
}

SENSITIVITY_REPORT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Sensitivity Report",
    "description": (
        "Schema for sensitivity analysis results regarding regression start times. "
        "Validates variance < 5% threshold as per spec.md SC-003 and US-2."
    ),
    "type": "object",
    "required": [
        "solvent", "total_trajectory_length_ps", "start_fractions",
        "points", "variance_percent", "variance_valid", "timestamp"
    ],
    "properties": {
        "solvent": {
            "type": "string",
            "enum": ["water", "ethanol", "acetone"],
            "description": "The solvent analyzed."
        },
        "total_trajectory_length_ps": {
            "type": "number",
            "description": "Total length of the trajectory in picoseconds."
        },
        "start_fractions": {
            "type": "array",
            "items": {"type": "number"},
            "description": (
                "List of start time fractions used for the sweep (0.1, 0.2, 0.3). "
                "Defined in Plan, spec.md SC-003, and US-2."
            )
        },
        "points": {
            "type": "array",
            "description": "List of sensitivity points for each start fraction.",
            "items": {
                "type": "object",
                "required": ["start_fraction", "start_time_ps", "diffusion_coefficient", "r_squared"],
                "properties": {
                    "start_fraction": {"type": "number"},
                    "start_time_ps": {"type": "number"},
                    "diffusion_coefficient": {
                        "type": "number",
                        "description": "Diffusion coefficient calculated at this start time."
                    },
                    "r_squared": {"type": "number"}
                }
            }
        },
        "variance_percent": {
            "type": "number",
            "description": (
                "Variance of diffusion coefficients across start times, "
                "expressed as a percentage."
            )
        },
        "variance_valid": {
            "type": "boolean",
            "description": (
                "True if variance_percent < 5.0, False otherwise. "
                "Threshold defined in spec.md SC-003."
            )
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of the analysis."
        },
        "summary": {
            "type": "string",
            "description": "Human-readable summary of the sensitivity analysis."
        }
    }
}

def generate_diffusion_results_schema() -> Dict[str, Any]:
    """Return the schema dictionary for diffusion results."""
    return DIFFUSION_RESULTS_SCHEMA

def generate_bootstrap_stats_schema() -> Dict[str, Any]:
    """Return the schema dictionary for bootstrap statistics."""
    return BOOTSTRAP_STATS_SCHEMA

def generate_sensitivity_report_schema() -> Dict[str, Any]:
    """Return the schema dictionary for sensitivity reports."""
    return SENSITIVITY_REPORT_SCHEMA

def write_schema(schema: Dict[str, Any], output_path: Path) -> None:
    """
    Write a schema dictionary to a YAML file.

    Args:
        schema: The schema dictionary to write.
        output_path: The path where the YAML file will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def main() -> None:
    """Main entry point to generate all contract schema files."""
    # Determine project root (assuming script is in code/utils/)
    # We want to write to code/contracts/
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    contracts_dir = project_root / "contracts"

    schemas = [
        (generate_diffusion_results_schema(), "diffusion_results.schema.yaml"),
        (generate_bootstrap_stats_schema(), "bootstrap_stats.schema.yaml"),
        (generate_sensitivity_report_schema(), "sensitivity_report.schema.yaml"),
    ]

    print(f"Generating schemas in {contracts_dir}...")
    for schema, filename in schemas:
        output_path = contracts_dir / filename
        write_schema(schema, output_path)
        print(f"  Written: {output_path}")

    print("Schema generation complete.")

if __name__ == "__main__":
    main()
