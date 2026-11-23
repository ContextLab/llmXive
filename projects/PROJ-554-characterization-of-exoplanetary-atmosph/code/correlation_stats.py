"""
Correlation Statistics Module for Exoplanetary Atmosphere Analysis.

This module implements functions to compute and save correlation statistics,
including Kendall's tau, p-values, and confidence intervals derived from
bootstrap resampling.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

# Import shared utilities
from utils import setup_logging, PipelineError
from config import get_config

# Configure logger
logger = setup_logging(__name__)


def load_correlation_results(input_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load correlation results from the bootstrap analysis.

    Expects a JSON file containing 'bootstrap_ci' with 'ci_lower', 'ci_upper',
    'tau_mean', and 'iterations', plus the primary 'tau' and 'p_value' from
    the censored Kendall's tau calculation.

    Args:
        input_path: Path to the bootstrap_ci.json file. Defaults to
                    data/processed/bootstrap_ci.json.

    Returns:
        Dictionary containing correlation statistics.

    Raises:
        PipelineError: If the file cannot be loaded or required keys are missing.
    """
    if input_path is None:
        config = get_config()
        input_path = str(config.data_processed_dir / "bootstrap_ci.json")

    path = Path(input_path)
    if not path.exists():
        raise PipelineError(f"Bootstrap results file not found: {path}")

    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise PipelineError(f"Failed to parse JSON from {path}: {e}")

    # Validate expected structure
    required_keys = ['tau', 'p_value', 'ci_lower', 'ci_upper', 'iterations']
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise PipelineError(f"Missing required keys in bootstrap_ci.json: {missing}")

    logger.info(f"Loaded correlation results from {path}")
    return data


def compute_ci_width(data: Dict[str, Any]) -> float:
    """
    Compute the width of the 95% confidence interval.

    Args:
        data: Dictionary containing 'ci_lower' and 'ci_upper'.

    Returns:
        Width of the confidence interval (ci_upper - ci_lower).
    """
    return data['ci_upper'] - data['ci_lower']


def save_correlation_stats(
    input_data: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """
    Save correlation statistics to a JSON file.

    This function takes the loaded correlation data and saves it to the
    specified output path. It ensures the output directory exists.

    Args:
        input_data: Dictionary containing 'tau', 'p_value', 'ci_lower',
                    'ci_upper', and 'iterations'.
        output_path: Path for the output JSON file. Defaults to
                     data/processed/correlation_stats.json.
    """
    if output_path is None:
        config = get_config()
        output_path = str(config.data_processed_dir / "correlation_stats.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure data is serializable (convert numpy types to native python)
    stats = {
        'tau': float(input_data['tau']),
        'p_value': float(input_data['p_value']),
        'ci_lower': float(input_data['ci_lower']),
        'ci_upper': float(input_data['ci_upper']),
        'iterations': int(input_data['iterations']),
        'ci_width': compute_ci_width(input_data)
    }

    try:
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Saved correlation statistics to {output_file}")
    except IOError as e:
        raise PipelineError(f"Failed to write correlation stats to {output_file}: {e}")


def main() -> None:
    """
    Main entry point for the correlation stats module.

    Loads the bootstrap results, computes the CI width, and saves the
    final correlation statistics to disk.
    """
    config = get_config()
    logger.info("Starting correlation stats generation...")

    try:
        # Load results from the bootstrap analysis (T025c)
        input_path = str(config.data_processed_dir / "bootstrap_ci.json")
        data = load_correlation_results(input_path)

        # Save the formatted stats (T030a)
        save_correlation_stats(data)

        logger.info("Correlation stats generation completed successfully.")

    except PipelineError as e:
        logger.error(f"Pipeline error during correlation stats generation: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during correlation stats generation: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()