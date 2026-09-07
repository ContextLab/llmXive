import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import get_logger, read_json, write_json, ensure_file_directory
from config import ensure_directories

# Configure logging
logger = get_logger("final_report")

def load_model_report() -> dict:
    """Load the primary model report."""
    path = project_root / "data" / "results" / "model_report.json"
    if not path.exists():
        logger.error(f"Model report not found at {path}")
        raise FileNotFoundError(f"Missing model report: {path}")
    return read_json(path)

def load_robustness_report() -> dict:
    """Load the robustness analysis report."""
    path = project_root / "data" / "results" / "robustness_report.json"
    if not path.exists():
        logger.error(f"Robustness report not found at {path}")
        raise FileNotFoundError(f"Missing robustness report: {path}")
    return read_json(path)

def load_diagnostics() -> dict:
    """Load collinearity diagnostics."""
    path = project_root / "data" / "results" / "diagnostics.json"
    if not path.exists():
        logger.error(f"Diagnostics not found at {path}")
        raise FileNotFoundError(f"Missing diagnostics: {path}")
    return read_json(path)

def load_delta_r2() -> dict:
    """Load the reduced model delta R2."""
    path = project_root / "data" / "results" / "delta_r2.json"
    if not path.exists():
        logger.error(f"Delta R2 not found at {path}")
        raise FileNotFoundError(f"Missing delta R2: {path}")
    return read_json(path)

def aggregate_results():
    """
    Aggregate all results into data/results/final_report.json.
    Combines Primary (Model), Null, and Robustness findings.
    """
    ensure_directories()
    output_path = project_root / "data" / "results" / "final_report.json"
    ensure_file_directory(output_path)

    try:
        logger.info("Loading Primary Model Report...")
        model_report = load_model_report()

        logger.info("Loading Robustness Report...")
        robustness_report = load_robustness_report()

        logger.info("Loading Diagnostics...")
        diagnostics = load_diagnostics()

        logger.info("Loading Delta R2...")
        delta_r2 = load_delta_r2()

        # Construct the final report
        final_report = {
            "project": "Resting-State fMRI Global Signal as a Marker of Mind-Wandering",
            "task_id": "T034a",
            "status": "complete",
            "components": {
                "primary_model": model_report,
                "null_distribution": model_report.get("null_distribution", {}),
                "robustness_analysis": robustness_report,
                "collinearity_diagnostics": diagnostics,
                "reduced_model_comparison": delta_r2
            },
            "summary": {
                "primary_metric": "Global_Signal_SD",
                "outcome": "MWQ_Score",
                "covariates": ["FD", "DVARS", "Age", "Sex"],
                "method": "Ridge Regression with Nested CV",
                "key_findings": {
                    "observed_mae": model_report.get("observed_mae"),
                    "observed_r": model_report.get("observed_r"),
                    "observed_r_squared": model_report.get("observed_r_squared"),
                    "empirical_p_value": model_report.get("empirical_p_value"),
                    "delta_r2": delta_r2.get("delta_r2"),
                    "max_vif": max(diagnostics.get("vif_values", {}).values()) if diagnostics.get("vif_values") else None
                },
                "robustness_check": {
                    "alpha_sweep_stable": robustness_report.get("alpha_sweep", {}).get("stable", False),
                    "variance_metric_correlation": robustness_report.get("variance_metric_analysis", {}).get("pearson_r"),
                    "partial_correlation_significant": robustness_report.get("partial_correlation", {}).get("significant", False)
                }
            }
        }

        logger.info(f"Writing final report to {output_path}")
        write_json(final_report, output_path)
        logger.info("Final report generated successfully.")

        return final_report

    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate final report: {e}")
        raise

def main():
    """Entry point for the final report aggregation."""
    ensure_directories()
    logger.info("Starting final report aggregation (T034a)...")
    try:
        result = aggregate_results()
        logger.info("T034a completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T034a failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
