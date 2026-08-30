import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import pandas as pd

# Import from existing API surface
from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config
from analysis.bootstrap import run_bootstrap_analysis
from analysis.sensitivity import run_sensitivity_analysis, apply_family_wise_error_correction
from analysis.collinearity_handler import check_collinearity_flags
from analysis.export_results import export_diagnostics_to_json

logger = get_logger(__name__)


def load_model_results() -> Dict[str, Any]:
    """
    Load regression coefficients and diagnostics from data/processed.
    Expects:
      - data/processed/regression_coefficients.csv
      - data/processed/regression_diagnostics.json
    """
    config = get_config()
    processed_dir = config["paths"]["processed"]
    
    coeffs_path = Path(processed_dir) / "regression_coefficients.csv"
    diagnostics_path = Path(processed_dir) / "regression_diagnostics.json"

    if not coeffs_path.exists():
        raise FileNotFoundError(f"Model coefficients not found: {coeffs_path}")
    if not diagnostics_path.exists():
        raise FileNotFoundError(f"Model diagnostics not found: {diagnostics_path}")

    # Load coefficients
    df_coeffs = pd.read_csv(coeffs_path)
    coeffs_dict = df_coeffs.to_dict(orient="records")

    # Load diagnostics
    with open(diagnostics_path, "r") as f:
        diagnostics = json.load(f)

    return {
        "coefficients": coeffs_dict,
        "diagnostics": diagnostics
    }


def load_bootstrap_results() -> Dict[str, Any]:
    """
    Load bootstrap stability results.
    Expects: data/processed/bootstrap_results.json
    """
    config = get_config()
    processed_dir = config["paths"]["processed"]
    bootstrap_path = Path(processed_dir) / "bootstrap_results.json"

    if not bootstrap_path.exists():
        logger.warning(f"Bootstrap results not found at {bootstrap_path}. Running analysis.")
        # Run bootstrap if missing
        run_bootstrap_analysis()
    
    with open(bootstrap_path, "r") as f:
        return json.load(f)


def load_sensitivity_results() -> Dict[str, Any]:
    """
    Load sensitivity analysis results.
    Expects: data/processed/sensitivity_results.json
    """
    config = get_config()
    processed_dir = config["paths"]["processed"]
    sensitivity_path = Path(processed_dir) / "sensitivity_results.json"

    if not sensitivity_path.exists():
        logger.warning(f"Sensitivity results not found at {sensitivity_path}. Running analysis.")
        # Run sensitivity if missing
        run_sensitivity_analysis()

    with open(sensitivity_path, "r") as f:
        return json.load(f)


def load_data_path() -> str:
    """
    Retrieve the data path used from the state file.
    Expects: state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml
    """
    config = get_config()
    state_path = Path(config["paths"]["state"]) / "projects" / "PROJ-490-the-effect-of-simulated-social-compariso.yaml"
    
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")

    import yaml
    with open(state_path, "r") as f:
        state_data = yaml.safe_load(f)

    # Extract artifact info
    artifacts = state_data.get("artifact_hashes", {})
    data_source = artifacts.get("data_source", {})
    return data_source.get("path", "Unknown")


def generate_final_report(
    model_results: Optional[Dict[str, Any]] = None,
    bootstrap_results: Optional[Dict[str, Any]] = None,
    sensitivity_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate the final report JSON containing:
    - data path used
    - model results
    - bootstrap stability
    - parameter recovery (if synthetic)
    - sensitivity findings
    """
    logger.info("Generating final report...")

    # Load data path
    data_path = load_data_path()

    # Load or use provided results
    if model_results is None:
        model_results = load_model_results()
    if bootstrap_results is None:
        bootstrap_results = load_bootstrap_results()
    if sensitivity_results is None:
        sensitivity_results = load_sensitivity_results()

    # Check for parameter recovery (synthetic data indicator)
    param_recovery = sensitivity_results.get("parameter_recovery", None)
    is_synthetic = param_recovery is not None and len(param_recovery) > 0

    # Assemble report
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "project_id": "PROJ-490-the-effect-of-simulated-social-compariso",
            "task_id": "T030",
            "data_source_path": data_path,
            "data_type": "synthetic" if is_synthetic else "real"
        },
        "model_results": {
            "coefficients": model_results["coefficients"],
            "assumptions_check": model_results["diagnostics"].get("assumptions", {}),
            "collinearity_flags": model_results["diagnostics"].get("collinearity_flags", [])
        },
        "bootstrap_stability": {
            "ci_width_variance": bootstrap_results.get("ci_width_variance"),
            "stability_flag": bootstrap_results.get("stability_flag"),
            "iterations": bootstrap_results.get("iterations")
        },
        "sensitivity_findings": {
            "threshold_sweep": sensitivity_results.get("threshold_sensitivity", {}),
            "imputation_limits": sensitivity_results.get("imputation_limits", {}),
            "error_correction_applied": sensitivity_results.get("family_wise_error_correction", {}),
            "parameter_recovery": param_recovery if is_synthetic else None
        },
        "conclusions": {
            "stability_assessment": "Stable" if bootstrap_results.get("stability_flag") == "PASS" else "UNSTABLE",
            "robustness_assessment": "Robust" if sensitivity_results.get("overall_robustness") == "PASS" else "SENSITIVE"
        }
    }

    return report


def save_report(report: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the report to a JSON file in data/processed.
    """
    config = get_config()
    processed_dir = config["paths"]["processed"]

    if output_path is None:
        output_path = Path(processed_dir) / "final_report.json"
    else:
        output_path = Path(output_path)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Final report saved to: {output_path}")
    return str(output_path)


def run_report_generation() -> str:
    """
    Main entry point for T030.
    Generates and saves the final report JSON.
    """
    log_execution_start(logger, "T030")

    try:
        # Generate report
        report = generate_final_report()

        # Save report
        output_path = save_report(report)

        log_execution_end(logger, "T030", success=True)
        return output_path

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        log_execution_end(logger, "T030", success=False)
        raise e


if __name__ == "__main__":
    run_report_generation()
