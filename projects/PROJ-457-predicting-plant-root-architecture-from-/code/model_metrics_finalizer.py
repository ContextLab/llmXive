"""
Task T029c: Write Final JSON for Model Metrics.

Reads the derived metrics calculated in T029b (from `artifacts/reports/metrics.json`
and `artifacts/sensitivity/sensitivity_analysis.json`) and writes the consolidated
final report to `artifacts/reports/model_metrics.json`.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import shared utilities from existing API surface
from config import get_config, setup_logging

# Ensure output directory exists
OUTPUT_DIR = Path("artifacts/reports")
OUTPUT_FILE = OUTPUT_DIR / "model_metrics.json"
METRICS_INPUT = OUTPUT_DIR / "metrics.json"
SENSITIVITY_INPUT = Path("artifacts/sensitivity/sensitivity_analysis.json")


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file, raising FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file with pretty printing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info(f"Successfully wrote metrics to {path}")


def generate_final_model_metrics_json() -> Dict[str, Any]:
    """
    Consolidate metrics from T029a, T029b, and T028c into the final JSON structure.
    
    Expected inputs:
    - artifacts/reports/metrics.json (contains lmm_r2, rf_r2, sc002_met, pn_availability_rate, etc.)
    - artifacts/sensitivity/sensitivity_analysis.json (contains sensitivity details)
    
    Returns:
    - A dictionary ready for serialization to model_metrics.json.
    """
    # Load prerequisite artifacts
    try:
        metrics_data = load_json_file(METRICS_INPUT)
    except FileNotFoundError as e:
        logging.error(f"Missing metrics data required for T029c: {e}")
        raise

    sensitivity_data = {}
    if SENSITIVITY_INPUT.exists():
        try:
            sensitivity_data = load_json_file(SENSITIVITY_INPUT)
        except Exception as e:
            logging.warning(f"Could not load sensitivity analysis for final report: {e}")
    else:
        logging.warning(f"Sensitivity analysis file not found at {SENSITIVITY_INPUT}. "
                        "Proceeding without sensitivity details.")

    # Construct the final report structure
    final_report = {
        "task_id": "T029c",
        "description": "Final Model Metrics Report",
        "model_performance": {
            "lmm": {
                "adjusted_r_squared": metrics_data.get("lmm_adjusted_r_squared"),
                "rmse": metrics_data.get("lmm_rmse"),
                "p_values": metrics_data.get("lmm_p_values", {}),
                "coefficients": metrics_data.get("lmm_coefficients", {})
            },
            "random_forest": {
                "r_squared": metrics_data.get("rf_r_squared"),
                "rmse": metrics_data.get("rf_rmse"),
                "n_estimators": metrics_data.get("rf_n_estimators", 100),
                "max_depth": metrics_data.get("rf_max_depth", 5)
            }
        },
        "derived_metrics": {
            "r2_difference": metrics_data.get("r2_difference"),
            "sc002_met": metrics_data.get("sc002_met", False),
            "pn_availability_rate": metrics_data.get("pn_availability_rate"),
            "species_exclusion_ratio": metrics_data.get("species_exclusion_ratio")
        },
        "sensitivity_analysis": sensitivity_data,
        "metadata": {
            "generated_by": "code/model_metrics_finalizer.py",
            "task_id": "T029c"
        }
    }

    # Clean up any None values for cleaner JSON output
    def remove_nones(obj):
        if isinstance(obj, dict):
            return {k: remove_nones(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [remove_nones(item) for item in obj if item is not None]
        else:
            return obj

    return remove_nones(final_report)


def main() -> None:
    """Entry point for T029c."""
    config = get_config()
    logger = setup_logging(__name__)
    logger.info("Starting T029c: Write Final JSON for Model Metrics")

    try:
        final_metrics = generate_final_model_metrics_json()
        save_json_file(OUTPUT_FILE, final_metrics)
        logger.info("T029c completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Critical input missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T029c: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()