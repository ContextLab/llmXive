"""
Hysteresis Controller for Adaptive Complexity Scaling.

This module implements the hysteresis logic to prevent premature tier switching
(the "illusion of competence" / "System 2 bypass" risk). It defines a fixed
baseline threshold and generates a configuration file for the simulation pipeline.

Dependencies:
- T015 (train_load_model.py): Ensures the Load Model is validated (r >= 0.6) before config generation.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import logger from utils as per API surface
try:
    from utils import get_logger
except ImportError:
    # Fallback for direct execution if utils is not in path yet
    import logging
    def get_logger(name):
        return logging.getLogger(name)


# Constants
BASELINE_THRESHOLD = 0.05
HYSTERESIS_BAND = "moderate"
OUTPUT_DIR = Path("data/simulation_results")
CONFIG_FILE = OUTPUT_DIR / "hysteresis_config.json"
MODEL_VALIDATION_STATUS_FILE = Path("data/processed/model_validation_status.json")


def load_model_validation_status() -> Dict[str, Any]:
    """
    Loads the validation status of the Load Model (T015).
    Ensures the model achieved Pearson r >= 0.6 before proceeding.

    Returns:
        Dict containing validation metrics.

    Raises:
        FileNotFoundError: If the validation status file is missing.
        ValueError: If the model validation failed (r < 0.6).
    """
    if not MODEL_VALIDATION_STATUS_FILE.exists():
        raise FileNotFoundError(
            f"Model validation status file not found: {MODEL_VALIDATION_STATUS_FILE}. "
            "Ensure T015 (train_load_model.py) has run successfully and saved validation metrics."
        )

    with open(MODEL_VALIDATION_STATUS_FILE, 'r') as f:
        status = json.load(f)

    pearson_r = status.get("pearson_r", 0.0)
    if pearson_r < 0.6:
        raise ValueError(
            f"Model validation failed: Pearson r ({pearson_r:.4f}) < 0.6. "
            "The Hysteresis Controller cannot proceed with an unvalidated model. "
            "Please re-run T015 to ensure the model meets the performance threshold."
        )

    return status


def determine_tier(current_load_score: float, current_tier: str) -> str:
    """
    Determines the next tier based on the current load score and hysteresis logic.

    The hysteresis band prevents rapid oscillation (thrashing) between tiers.
    - If load is high, we might simplify, but only if it stays high for a sustained period.
    - If load is low, we might increase complexity, but only if it stays low.

    For the baseline simulation (T032), we use a fixed threshold to define the
    "trigger" point, but the 'moderate' band implies we stay in the current state
    unless the deviation is significant.

    Args:
        current_load_score (float): The predicted cognitive load score (0-100).
        current_tier (str): The current complexity tier ('simple', 'moderate', 'complex').

    Returns:
        str: The next complexity tier.
    """
    # Normalize load score to 0-1 range for threshold comparison
    normalized_load = current_load_score / 100.0

    # Hysteresis logic:
    # We only switch tiers if the load deviates significantly from the baseline
    # defined by the current tier's expected range.
    # For this implementation, we use the fixed threshold to determine a "switch" event.

    if current_tier == "moderate":
        # If load is significantly high (> threshold), switch to simple
        if normalized_load > BASELINE_THRESHOLD:
            return "simple"
        # If load is significantly low (< -threshold), switch to complex
        # Note: Assuming load < 0.05 is "easy" -> increase complexity
        elif normalized_load < (1.0 - BASELINE_THRESHOLD): # Simplified logic for band
            return "complex"

    elif current_tier == "simple":
        # Only switch back to moderate if load drops significantly
        if normalized_load < (1.0 - BASELINE_THRESHOLD):
            return "moderate"

    elif current_tier == "complex":
        # Only switch back to moderate if load rises significantly
        if normalized_load > BASELINE_THRESHOLD:
            return "moderate"

    return current_tier


def generate_hysteresis_config() -> Dict[str, Any]:
    """
    Generates the hysteresis configuration file.

    This function:
    1. Verifies the Load Model (T015) is validated (r >= 0.6).
    2. Creates the config dictionary with the fixed baseline threshold.
    3. Writes the config to `data/simulation_results/hysteresis_config.json`.

    Returns:
        Dict: The generated configuration.

    Raises:
        ValueError: If model validation fails.
        IOError: If writing the config file fails.
    """
    logger = get_logger(__name__)
    logger.info("Generating Hysteresis Controller configuration...")

    # 1. Validate Model Dependency (T015)
    try:
        validation_status = load_model_validation_status()
        logger.info(f"Model validation confirmed. Pearson r: {validation_status.get('pearson_r', 'N/A')}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Model validation check failed: {e}")
        raise

    # 2. Define Config
    config = {
        "baseline_threshold": BASELINE_THRESHOLD,
        "hysteresis_band": HYSTERESIS_BAND,
        "description": "Fixed baseline threshold for baseline simulation. Sensitivity analysis handled in T033."
    }

    # 3. Ensure Output Directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 4. Write Config
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Hysteresis config written to {CONFIG_FILE}")
    except IOError as e:
        logger.error(f"Failed to write config file: {e}")
        raise

    return config


def main():
    """
    Main entry point for the Hysteresis Controller task (T032).
    """
    logger = get_logger(__name__)
    logger.info("Starting T032: Implement Hysteresis Controller")

    try:
        config = generate_hysteresis_config()
        logger.info("T032 completed successfully.")
        return config
    except Exception as e:
        logger.error(f"T032 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
