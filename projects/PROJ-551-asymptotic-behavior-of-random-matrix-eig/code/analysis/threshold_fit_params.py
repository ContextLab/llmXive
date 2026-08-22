"""
Task T022c: Write fitted parameters to data/processed/threshold_fit_params.json.

This module loads the fitted critical threshold parameters derived from the
logistic regression/sigmoid fitting (performed in T022a/T022b) and writes them
to a JSON artifact for downstream analysis and reporting.

It relies on the `fit_critical_threshold` function in `fit_utils` which returns
the fitted parameters (theta_c, slope, intercept) and the fit quality metrics.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils.config import get_project_paths
from analysis.fit_utils import fit_critical_threshold, load_mc_results, aggregate_by_theta

logger = logging.getLogger(__name__)

def load_fitted_parameters() -> Dict[str, Any]:
    """
    Loads Monte Carlo results, aggregates by theta, performs the fit,
    and returns the fitted parameters and metadata.

    Returns:
        Dict containing fitted parameters and metadata.
    """
    paths = get_project_paths()
    mc_results_path = paths["data_processed"] / "mc_results.csv"

    if not mc_results_path.exists():
        raise FileNotFoundError(
            f"Monte Carlo results file not found at {mc_results_path}. "
            "Ensure T021a has been executed successfully."
        )

    logger.info(f"Loading Monte Carlo results from {mc_results_path}")
    mc_data = load_mc_results(mc_results_path)

    if not mc_data:
        raise ValueError("Monte Carlo results file is empty or invalid.")

    logger.info("Aggregating results by theta")
    aggregated = aggregate_by_theta(mc_data)

    if not aggregated:
        raise ValueError("No valid data aggregated for fitting.")

    logger.info("Fitting critical threshold")
    fit_result = fit_critical_threshold(aggregated)

    if fit_result is None:
        raise RuntimeError("Fitting critical threshold failed. Check fit_utils implementation.")

    return fit_result

def write_fit_parameters(output_path: Optional[Path] = None) -> Path:
    """
    Writes the fitted parameters to a JSON file.

    Args:
        output_path: Optional path to write the JSON file. Defaults to
                     data/processed/threshold_fit_params.json.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = paths["data_processed"] / "threshold_fit_params.json"

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        params = load_fitted_parameters()

        # Add timestamp and source info
        from datetime import datetime, timezone
        params["generated_at"] = datetime.now(timezone.utc).isoformat()
        params["source_file"] = str(output_path.parent / "mc_results.csv")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2)

        logger.info(f"Fitted parameters written to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Failed to write fitted parameters: {e}", exc_info=True)
        raise

def main():
    """Entry point for running the parameter writing script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info("Starting T022c: Writing fitted parameters")

    try:
        output_path = write_fit_parameters()
        logger.info(f"Success. Output file: {output_path}")
    except Exception as e:
        logger.critical(f"Task T022c failed: {e}")
        raise

if __name__ == "__main__":
    main()
