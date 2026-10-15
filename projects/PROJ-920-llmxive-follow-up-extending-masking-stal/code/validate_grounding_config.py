"""
validate_grounding_config.py

This script validates that the simulation configuration respects the
project's Constitution VI, which mandates that semantic density is grounded
as a weighted combination of Shannon entropy and technical token ratio,
with the entropy weight strictly greater than the technical weight.

It also performs generic sanity checks on other simulation parameters
(alpha, threshold, density_levels) to ensure they are within sensible
ranges.

Usage:
    python code/validate_grounding_config.py [--config path/to/config.json]

The script exits with status 0 if the configuration passes all checks,
otherwise it prints descriptive error messages and exits with a non‑zero
status code.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Configure a simple logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Default location of the simulation configuration file
DEFAULT_CONFIG_PATH = Path("code/config/simulation_config.json")


def load_config(path: Path) -> Dict[str, Any]:
    """Load a JSON configuration file."""
    if not path.exists():
        logger.error(f"Configuration file not found: {path}")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Malformed JSON in configuration file {path}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error while reading {path}: {e}")
        sys.exit(1)


def _check_required_keys(config: Dict[str, Any], required: List[str]) -> List[str]:
    """Return a list of missing required keys."""
    missing = [key for key in required if key not in config]
    return missing


def validate_alpha(alpha: Any) -> Tuple[bool, str]:
    """Alpha must be a positive number."""
    if not isinstance(alpha, (int, float)):
        return False, "alpha must be numeric"
    if alpha <= 0:
        return False, "alpha must be > 0"
    return True, ""


def validate_threshold(threshold: Any) -> Tuple[bool, str]:
    """
    Threshold must be a number in a plausible range.
    The density values produced by the generator lie roughly between 0 and 1
    (see TARGET_DENSITIES in generate_trajectories.py).  Allow a small margin.
    """
    if not isinstance(threshold, (int, float)):
        return False, "threshold must be numeric"
    if not (0.0 <= threshold <= 2.0):
        return (
            False,
            "threshold outside expected range [0.0, 2.0]; "
            "adjust according to density scaling used in the pipeline",
        )
    return True, ""


def validate_density_weights(weights: Any) -> Tuple[bool, str]:
    """
    The Constitution VI requires:
    - The weights must be a mapping with keys 'entropy' and 'technical'.
    - Both values must be non‑negative numbers.
    - They must sum to 1 (or close to it, allowing tiny floating‑point error).
    - The entropy weight must be strictly greater than the technical weight.
    """
    if not isinstance(weights, dict):
        return False, "density_weights must be a dict"

    required_keys = {"entropy", "technical"}
    if set(weights.keys()) != required_keys:
        return (
            False,
            f"density_weights must contain exactly the keys {required_keys}",
        )

    entropy_w = weights.get("entropy")
    technical_w = weights.get("technical")

    if not isinstance(entropy_w, (int, float)) or not isinstance(
        technical_w, (int, float)
    ):
        return False, "density_weights values must be numeric"

    if entropy_w < 0 or technical_w < 0:
        return False, "density_weights values must be non‑negative"

    total = entropy_w + technical_w
    if abs(total - 1.0) > 1e-6:
        return False, f"weights must sum to 1 (got {total})"

    if entropy_w <= technical_w:
        return (
            False,
            "entropy weight must be strictly greater than technical weight "
            f"(got entropy={entropy_w}, technical={technical_w})",
        )

    return True, ""


def validate_density_levels(levels: Any) -> Tuple[bool, str]:
    """Density levels should be a list of strings containing at least low, medium, high."""
    if not isinstance(levels, list):
        return False, "density_levels must be a list"
    if not all(isinstance(v, str) for v in levels):
        return False, "density_levels must contain strings only"
    required = {"low", "medium", "high"}
    if not required.issubset(set(levels)):
        return (
            False,
            f"density_levels must include at least {required}",
        )
    return True, ""


def validate_seed(seed: Any) -> Tuple[bool, str]:
    """Seed must be an integer >= 0."""
    if not isinstance(seed, int):
        return False, "seed must be an integer"
    if seed < 0:
        return False, "seed must be non‑negative"
    return True, ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that the simulation configuration respects Constitution VI "
            "and basic sanity constraints."
        )
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the simulation configuration JSON file.",
    )
    args = parser.parse_args()
    config_path = Path(args.config)

    config = load_config(config_path)

    # Define required top‑level keys for the simulation config
    required_keys = ["alpha", "threshold", "seed", "density_levels"]
    missing = _check_required_keys(config, required_keys)
    if missing:
        logger.error(f"Configuration missing required keys: {missing}")
        sys.exit(1)

    # Validate each field
    validators = {
        "alpha": validate_alpha,
        "threshold": validate_threshold,
        "seed": validate_seed,
        "density_levels": validate_density_levels,
    }

    errors: List[str] = []

    for key, validator in validators.items():
        ok, msg = validator(config[key])
        if not ok:
            errors.append(f"{key}: {msg}")

    # Optional Constitution‑VI‑specific check for density weighting
    if "density_weights" in config:
        ok, msg = validate_density_weights(config["density_weights"])
        if not ok:
            errors.append(f"density_weights: {msg}")

    if errors:
        logger.error("Configuration validation failed with the following issues:")
        for e in errors:
            logger.error(f"  - {e}")
        sys.exit(1)

    logger.info("Simulation configuration passed all validation checks.")
    sys.exit(0)


if __name__ == "__main__":
    main()