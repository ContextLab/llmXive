"""
Regression Statistics Calculation and Reporting (Task T030b)

Implements save_regression_stats to extract regression coefficients, p-values,
and model fit statistics from the Tobit/Ridge regression results and save them
to data/processed/regression_stats.json.

Dependencies:
  - code/analysis_tobit.py (provides save_regression_results -> data/processed/regression_results.json)
  - code/config.py (for configuration)
  - code/utils.py (for logging)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging

# Configure logger
logger = setup_logging(__name__)


def load_regression_results(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the regression results from the JSON file produced by analysis_tobit.py.

    Args:
        input_path: Path to the regression_results.json file. Defaults to
                    data/processed/regression_results.json if not provided.

    Returns:
        Dictionary containing regression results (coefficients, p-values, etc.)

    Raises:
        FileNotFoundError: If the regression results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        config = get_config()
        input_path = config["paths"]["processed"] / "regression_results.json"

    if not input_path.exists():
        logger.error(f"Regression results file not found: {input_path}")
        raise FileNotFoundError(f"Regression results file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    logger.info(f"Loaded regression results from {input_path}")
    return data


def compute_regression_stats(regression_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute and format regression statistics from the raw regression data.

    Extracts coefficients, p-values, model fit metrics (R-squared, AIC, BIC),
    and any fallback flags from the regression results.

    Args:
        regression_data: Dictionary containing the raw regression results.

    Returns:
        Dictionary containing formatted regression statistics.
    """
    stats = {
        "model_type": "Tobit",
        "fallback_triggered": regression_data.get("fallback_triggered", False),
        "coefficients": {},
        "p_values": {},
        "model_fit": {},
        "sample_size": regression_data.get("sample_size", 0),
        "censored_count": regression_data.get("censored_count", 0),
        "uncensored_count": regression_data.get("uncensored_count", 0)
    }

    # Extract coefficients and p-values
    if "coefficients" in regression_data:
        coef_dict = regression_data["coefficients"]
        for var, val in coef_dict.items():
            stats["coefficients"][var] = float(val) if isinstance(val, (int, float, np.floating, np.integer)) else val

    if "p_values" in regression_data:
        pval_dict = regression_data["p_values"]
        for var, val in pval_dict.items():
            stats["p_values"][var] = float(val) if isinstance(val, (int, float, np.floating, np.integer)) else val

    # Extract model fit metrics
    if "model_fit" in regression_data:
        fit_dict = regression_data["model_fit"]
        for metric, val in fit_dict.items():
            stats["model_fit"][metric] = float(val) if isinstance(val, (int, float, np.floating, np.integer)) else val

    # Add fallback details if triggered
    if stats["fallback_triggered"] and "fallback_details" in regression_data:
        stats["fallback_details"] = regression_data["fallback_details"]

    logger.info(f"Computed regression statistics for {stats['sample_size']} samples "
                f"({stats['censored_count']} censored, {stats['uncensored_count']} uncensored)")

    return stats


def save_regression_stats(stats: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the computed regression statistics to a JSON file.

    Args:
        stats: Dictionary containing the regression statistics.
        output_path: Path to the output JSON file. Defaults to
                     data/processed/regression_stats.json if not provided.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        config = get_config()
        output_path = config["paths"]["processed"] / "regression_stats.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)

    logger.info(f"Saved regression statistics to {output_path}")
    return output_path


def main():
    """
    Main entry point for the regression statistics task.

    1. Loads regression results from data/processed/regression_results.json
    2. Computes formatted statistics
    3. Saves results to data/processed/regression_stats.json
    """
    logger.info("Starting regression statistics calculation (T030b)")

    try:
        # Load regression results
        regression_data = load_regression_results()

        # Compute statistics
        stats = compute_regression_stats(regression_data)

        # Save results
        output_path = save_regression_stats(stats)

        logger.info(f"Regression statistics task completed successfully. Output: {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Failed to find required input file: {e}")
        logger.error("Ensure that T027 (fit_tobit_model) has run and produced data/processed/regression_results.json")
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred during regression statistics calculation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())