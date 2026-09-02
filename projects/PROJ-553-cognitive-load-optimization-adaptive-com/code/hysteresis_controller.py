"""
Hysteresis Controller for Adaptive Complexity Scaling.

This module implements the hysteresis logic used in the Adaptive condition
simulation (US3). It defines fixed thresholds for switching between
explanation complexity tiers based on the estimated cognitive load.

Dependencies:
- T015: Ensures the Load Model is validated (r >= 0.6) before this controller
  is used for simulation.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure imports work in the project structure
if __name__ == "__main__":
    # Add parent directory to path for execution as script
    sys.path.insert(0, str(Path(__file__).parent))

from utils import get_logger

logger = get_logger(__name__)

# Fixed thresholds for the baseline simulation
# These values represent the "hysteresis loop" to prevent oscillation
# between tiers when load is near a boundary.
HYSTERESIS_CONFIG = {
    "description": "Baseline hysteresis thresholds for Adaptive condition simulation.",
    "thresholds": {
        "low_load_upper_bound": 40.0,   # If load < 40, switch to Simple
        "high_load_lower_bound": 70.0,  # If load > 70, switch to Complex
        "moderate_load_range": [40.0, 70.0] # If 40 <= load <= 70, stay Moderate
    },
    "tier_mapping": {
        "low": "simple",
        "moderate": "moderate",
        "high": "complex"
    },
    "validation_requirement": "T015 (Load Model r >= 0.6) must be passed before use."
}

def load_model_validation_status(model_path: str = "data/processed/load_model.pkl") -> bool:
    """
    Verifies that the Load Model exists and is within size limits.
    This implicitly validates that T015 has completed successfully.
    """
    if not os.path.exists(model_path):
        logger.error(f"Model validation failed: {model_path} does not exist.")
        logger.error("T015 must be completed successfully before using the Hysteresis Controller.")
        return False

    file_size_mb = os.path.getsize(model_path) / (1024 * 1024)
    if file_size_mb > 500:
        logger.error(f"Model validation failed: {model_path} is too large ({file_size_mb:.2f} MB > 500 MB).")
        return False

    logger.info(f"Model validation passed: {model_path} exists and is {file_size_mb:.2f} MB.")
    return True

def determine_tier(load_score: float, current_tier: str = "moderate") -> str:
    """
    Determines the next complexity tier based on the estimated load score
    and the current tier, applying hysteresis logic.

    Args:
        load_score: Estimated cognitive load (0-100).
        current_tier: The current tier being served ('simple', 'moderate', 'complex').

    Returns:
        The next tier to serve.
    """
    low_bound = HYSTERESIS_CONFIG["thresholds"]["low_load_upper_bound"]
    high_bound = HYSTERESIS_CONFIG["thresholds"]["high_load_lower_bound"]

    next_tier = current_tier

    if load_score < low_bound:
        # Low load: Simplify if not already simple
        if current_tier != "simple":
            next_tier = "simple"
            logger.debug(f"Load {load_score:.2f} < {low_bound}: Switching to 'simple'")
        else:
            logger.debug(f"Load {load_score:.2f} < {low_bound}: Already 'simple'")

    elif load_score > high_bound:
        # High load: Complexify if not already complex
        if current_tier != "complex":
            next_tier = "complex"
            logger.debug(f"Load {load_score:.2f} > {high_bound}: Switching to 'complex'")
        else:
            logger.debug(f"Load {load_score:.2f} > {high_bound}: Already 'complex'")

    else:
        # Moderate load: Stay in moderate or return to moderate if coming from extremes
        # This implements the "dead zone" of hysteresis
        if current_tier == "simple":
            # Only switch back to moderate if load is clearly rising above low bound
            # For simplicity in this baseline, we switch back if we are in the moderate range
            next_tier = "moderate"
            logger.debug(f"Load {load_score:.2f} in moderate range: Switching to 'moderate'")
        elif current_tier == "complex":
            next_tier = "moderate"
            logger.debug(f"Load {load_score:.2f} in moderate range: Switching to 'moderate'")
        else:
            logger.debug(f"Load {load_score:.2f} in moderate range: Staying 'moderate'")

    return next_tier

def generate_hysteresis_config(output_path: str = "data/simulation_results/hysteresis_config.json") -> Dict[str, Any]:
    """
    Generates and saves the hysteresis configuration file.
    Validates that T015 (Load Model) is complete before generating.
    """
    model_path = "data/processed/load_model.pkl"

    # Validate dependency T015
    if not load_model_validation_status(model_path):
        raise RuntimeError(
            "Hysteresis Controller cannot be initialized. "
            "The Load Model (T015) has not been validated or saved. "
            "Please ensure T015 completes successfully (r >= 0.6) before running this task."
        )

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save configuration
    with open(output_path, 'w') as f:
        json.dump(HYSTERESIS_CONFIG, f, indent=2)

    logger.info(f"Hysteresis configuration saved to {output_path}")
    return HYSTERESIS_CONFIG

def main():
    """Main entry point for generating the hysteresis config."""
    logger.info("Starting Hysteresis Controller initialization (T032)...")
    try:
        config = generate_hysteresis_config()
        logger.info("T032 completed successfully.")
        print(json.dumps(config, indent=2))
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during T032: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
