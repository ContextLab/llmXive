"""
Module: code/analysis/define_lift.py

Purpose:
    Implements Task T017a: Define the lift threshold for success criteria.
    Reads the power analysis results from `data/results/power_analysis.json`.
    Calculates a lift threshold based on the effect size (Cohen's w) or sample size.
    Writes the threshold (or 'DEFERRED' if data is missing) to
    `data/results/power_analysis_threshold.json`.

Constraints:
    - Does NOT modify `code/config.py`.
    - Does NOT use synthetic data.
    - Fails loudly if `power_analysis.json` is missing or malformed.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import logging setup from project utilities
try:
    from logging_config import get_logger, log_event
except ImportError:
    # Fallback for direct execution if logging_config is not in path
    logging.basicConfig(level=logging.INFO)
    def get_logger(name): return logging.getLogger(name)
    def log_event(*args, **kwargs): pass

# Import path utilities
try:
    from config import get_path_results, get_path_relative
except ImportError:
    from pathlib import Path
    def get_path_results():
        return Path(__file__).parent.parent.parent / "data" / "results"
    def get_path_relative(p):
        return p

logger = get_logger(__name__)

POWER_ANALYSIS_INPUT = "power_analysis.json"
THRESHOLD_OUTPUT = "power_analysis_threshold.json"


def load_power_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Loads the power analysis results from the data/results directory.

    Returns:
        Dict containing power analysis metrics, or None if file is missing.

    Raises:
        FileNotFoundError: If the power analysis file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    input_path = get_path_results() / POWER_ANALYSIS_INPUT

    if not input_path.exists():
        logger.error(f"Power analysis file not found at {input_path}. "
                     "Cannot define lift threshold without power metrics.")
        # We raise here to fail loudly as per constraints, rather than returning None
        # which might lead to silent failures downstream.
        raise FileNotFoundError(f"Required input file missing: {input_path}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded power analysis from {input_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in power analysis file: {e}")
        raise


def calculate_lift_threshold(power_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the lift threshold based on power analysis metrics.

    Logic:
        - If 'effect_size_w' (Cohen's w) is present, the lift threshold is typically
          derived from this. A common heuristic for 'meaningful lift' in classification
          over a baseline is often tied to the effect size.
          Here we define the threshold as the effect size itself (or a fraction if specified).
        - If 'sample_size' is present but no effect size, we might defer or use a default.
        - If data is insufficient, return 'DEFERRED'.

    Args:
        power_data: Dictionary loaded from power_analysis.json.

    Returns:
        Dictionary with 'threshold' (float or 'DEFERRED') and 'source' explanation.
    """
    result = {
        "threshold": "DEFERRED",
        "source": "insufficient_data",
        "details": {}
    }

    # Check for effect size (Cohen's w)
    effect_size = power_data.get("effect_size_w") or power_data.get("effect_size")

    if effect_size is not None:
        try:
            w = float(effect_size)
            # For a classification task, a lift threshold is often set to ensure
            # the model performs significantly better than the baseline.
            # We set the threshold to the effect size w, representing the minimum
            # standardized difference we powered for.
            # Alternatively, some definitions use w * baseline_rate, but w is the
            # direct metric of "lift" in power terms.
            result["threshold"] = w
            result["source"] = "effect_size_w"
            result["details"]["effect_size_used"] = w
            logger.info(f"Calculated lift threshold from effect size: {w}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse effect_size_w: {e}. Deferring threshold.")
            result["threshold"] = "DEFERRED"
            result["source"] = "invalid_effect_size"
            result["details"]["error"] = str(e)
    else:
        # Check if we have enough sample size to at least attempt a default
        sample_size = power_data.get("sample_size") or power_data.get("n_total")

        if sample_size is not None:
            result["details"]["sample_size_available"] = sample_size
            result["details"]["note"] = "No effect size provided; threshold deferred."
            logger.warning("Power analysis missing effect size. Threshold set to DEFERRED.")
        else:
            result["details"]["note"] = "No sample size or effect size found."

    return result


def update_config_with_lift_threshold(threshold_data: Dict[str, Any]) -> None:
    """
    Writes the calculated threshold data to the output JSON file.

    Args:
        threshold_data: Dictionary containing the threshold and metadata.
    """
    output_path = get_path_results() / THRESHOLD_OUTPUT

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(threshold_data, f, indent=2)

    logger.info(f"Wrote lift threshold result to {output_path}")


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("Starting lift threshold definition (T017a)...")

        # 1. Load Power Analysis
        power_data = load_power_analysis_results()

        # 2. Calculate Threshold
        threshold_result = calculate_lift_threshold(power_data)

        # 3. Write Output
        update_config_with_lift_threshold(threshold_result)

        if threshold_result["threshold"] == "DEFERRED":
            logger.warning("Lift threshold is DEFERRED. Downstream tasks must handle this.")
            return 0 # Still a successful run of the script, just a deferred value
        else:
            logger.info(f"Lift threshold defined successfully: {threshold_result['threshold']}")
            return 0

    except FileNotFoundError as e:
        logger.critical(f"Failed to define lift threshold: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.critical(f"Failed to parse power analysis: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error in define_lift: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())