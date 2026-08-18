"""
Task T030a: Output correlation statistics.

Computes and saves Kendall's tau, p-values, and CI width to data/processed/correlation_stats.json.
Relies on data produced by T025b (compute_censored_kendall_tau) and T025c (run_bootstrap_ci).
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging

logger = logging.getLogger(__name__)

def load_correlation_results() -> Dict[str, Any]:
    """
    Load the Kendall's tau and p-value from the analysis results.
    Assumes T025b has written the results to a JSON file or they are available
    via a standard location. For this implementation, we assume the results
    are stored in data/processed/analysis_intermediate.json or similar,
    or we recompute if necessary.

    However, based on the task dependencies, T025b computes the tau and p-value.
    T025c computes the bootstrap CI.
    T026 computes the CI width of water mixing ratio.

    We need to load:
    1. Kendall's tau and p-value (from T025b output)
    2. Bootstrap CI width for the correlation (from T025c output)

    Since the exact output file names for T025b and T025c are not explicitly
    defined in the task list, we assume:
    - T025b writes to: data/processed/kendall_tau_results.json
    - T025c writes to: data/processed/bootstrap_ci.json (which contains ci_lower, ci_upper for the correlation)

    If these files do not exist, we raise an error as the prerequisites are not met.
    """
    config = get_config()
    processed_dir = config["paths"]["processed"]

    # Load Kendall's tau results
    kendall_path = Path(processed_dir) / "kendall_tau_results.json"
    if not kendall_path.exists():
        raise FileNotFoundError(
            f"Prerequisite file missing: {kendall_path}. "
            "Ensure T025b has been executed successfully."
        )
    
    with open(kendall_path, "r") as f:
        kendall_data = json.load(f)

    # Load bootstrap CI results
    bootstrap_path = Path(processed_dir) / "bootstrap_ci.json"
    if not bootstrap_path.exists():
        raise FileNotFoundError(
            f"Prerequisite file missing: {bootstrap_path}. "
            "Ensure T025c has been executed successfully."
        )

    with open(bootstrap_path, "r") as f:
        bootstrap_data = json.load(f)

    return {
        "kendall_tau": kendall_data,
        "bootstrap_ci": bootstrap_data
    }

def compute_ci_width(ci_lower: float, ci_upper: float) -> float:
    """Compute the width of the confidence interval."""
    return ci_upper - ci_lower

def save_correlation_stats(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Aggregate correlation statistics and save to JSON.

    The output includes:
    - kendall_tau: The correlation coefficient
    - p_value: The p-value associated with the correlation
    - ci_lower: Lower bound of the 95% CI
    - ci_upper: Upper bound of the 95% CI
    - ci_width: The width of the CI (ci_upper - ci_lower)

    Returns the saved dictionary.
    """
    config = get_config()
    processed_dir = Path(config["paths"]["processed"])
    
    if output_path is None:
        output_path = processed_dir / "correlation_stats.json"
    else:
        output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        results = load_correlation_results()
        
        kendall_data = results["kendall_tau"]
        bootstrap_data = results["bootstrap_ci"]

        # Extract values
        tau = kendall_data.get("tau")
        p_value = kendall_data.get("p_value")
        
        # Bootstrap CI might be for the correlation or for the water mixing ratio.
        # Based on T025c description: "bootstrap resampling loop to estimate confidence intervals"
        # and T026: "Compute and report the CI width of the water mixing ratio distribution"
        # We assume T025c produced a CI for the correlation coefficient (Kendall's tau).
        # If T025c produced CI for water mixing ratio, we need to adjust.
        # Given T026 specifically handles water mixing ratio CI width, T025c likely handles correlation CI.
        
        ci_lower = bootstrap_data.get("ci_lower")
        ci_upper = bootstrap_data.get("ci_upper")
        iterations = bootstrap_data.get("iterations", 1000)

        if tau is None or p_value is None or ci_lower is None or ci_upper is None:
            raise ValueError("Missing required fields in prerequisite result files.")

        ci_width = compute_ci_width(ci_lower, ci_upper)

        output_data = {
            "kendall_tau": tau,
            "p_value": p_value,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "ci_width": ci_width,
            "bootstrap_iterations": iterations
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Correlation statistics saved to {output_path}")
        logger.info(f"Kendall's tau: {tau:.4f}, p-value: {p_value:.4f}, CI Width: {ci_width:.4f}")

        return output_data

    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error saving correlation statistics: {e}")
        raise

def main():
    """Main entry point for T030a."""
    setup_logging()
    logger.info("Starting Task T030a: Output correlation statistics")
    
    try:
        stats = save_correlation_stats()
        logger.info("Task T030a completed successfully")
    except Exception as e:
        logger.critical(f"Task T030a failed: {e}")
        raise

if __name__ == "__main__":
    main()