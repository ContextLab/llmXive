"""
T025: Write results to data/processed/cooperative_effects_analysis.json including
coefficients, p-values, and MSE reduction stats.

Dependencies:
  - T021c (statistical_validation.py) -> data/processed/statistical_validation_report.json
  - T022-Exec (compute_mse_reduction.py) -> data/processed/mse_comparison.json
  - T023-Exec (significance_test.py) -> data/processed/significance_results.json
  - T021b (regression.py) -> data/processed/regression_results.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from code.config import PROCESSED_PATH, get_logger

# Ensure output directory exists
PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file safely."""
    if not path.exists():
        logger.error(f"Required input file missing: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return None

def write_cooperative_analysis() -> bool:
    """
    Aggregate results from statistical validation, MSE comparison, significance testing,
    and regression analysis into a single comprehensive report.
    """
    # Define input paths
    validation_path = PROCESSED_PATH / "statistical_validation_report.json"
    mse_path = PROCESSED_PATH / "mse_comparison.json"
    significance_path = PROCESSED_PATH / "significance_results.json"
    regression_path = PROCESSED_PATH / "regression_results.json"

    # Load all required inputs
    validation_data = load_json(validation_path)
    mse_data = load_json(mse_path)
    significance_data = load_json(significance_path)
    regression_data = load_json(regression_path)

    # Validate that all inputs are present
    missing_inputs = []
    if validation_data is None:
        missing_inputs.append(str(validation_path))
    if mse_data is None:
        missing_inputs.append(str(mse_path))
    if significance_data is None:
        missing_inputs.append(str(significance_path))
    if regression_data is None:
        missing_inputs.append(str(regression_path))

    if missing_inputs:
        logger.critical(f"Cannot generate cooperative effects analysis. Missing inputs: {missing_inputs}")
        return False

    # Aggregate data into final report structure
    analysis_report = {
        "summary": {
            "cooperative_effects_detected": validation_data.get("status", "Unknown") == "Cooperative Effects Detected",
            "statistical_power": validation_data.get("cv_stability", {}).get("passed", False),
            "significance_threshold": 0.05,
            "mse_reduction_threshold": 0.10
        },
        "mse_reduction_stats": {
            "overall_reduction_percent": mse_data.get("overall_reduction_percent", 0.0),
            "systems_analyzed": mse_data.get("systems_analyzed", []),
            "threshold_met": mse_data.get("overall_reduction_percent", 0.0) >= 10.0
        },
        "interaction_coefficients": regression_data.get("coefficients", {}),
        "p_values": significance_data.get("p_values", {}),
        "significant_interactions": [
            term for term, p_val in significance_data.get("p_values", {}).items()
            if p_val < 0.05
        ],
        "system_details": []
    }

    # Build system-level details
    systems = set()
    if "systems" in mse_data:
        systems.update(mse_data["systems"])
    if "systems" in significance_data:
        systems.update(significance_data["systems"])

    for system in systems:
        system_entry = {
            "system_name": system,
            "mse_reduction_percent": next(
                (s["reduction_percent"] for s in mse_data.get("systems", []) if s["system"] == system),
                None
            ),
            "significant_interactions": [
                term for term, p_val in significance_data.get("p_values", {}).items()
                if term.startswith(system.replace("-", "_")) and p_val < 0.05
            ],
            "coefficient_values": {
                k: v for k, v in regression_data.get("coefficients", {}).items()
                if k.startswith(system.replace("-", "_"))
            },
            "p_value_values": {
                k: v for k, v in significance_data.get("p_values", {}).items()
                if k.startswith(system.replace("-", "_"))
            }
        }
        analysis_report["system_details"].append(system_entry)

    # Sort system details by name for consistency
    analysis_report["system_details"].sort(key=lambda x: x["system_name"])

    # Write final output
    output_path = PROCESSED_PATH / "cooperative_effects_analysis.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_report, f, indent=2, sort_keys=True)
        logger.info(f"Successfully wrote cooperative effects analysis to {output_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to write output file {output_path}: {e}")
        return False

def main():
    """Entry point for T025 execution."""
    logger.info("Starting T025: Write cooperative effects analysis")
    success = write_cooperative_analysis()
    if not success:
        logger.critical("T025 failed due to missing inputs or write error")
        sys.exit(1)
    logger.info("T025 completed successfully")

if __name__ == "__main__":
    main()
