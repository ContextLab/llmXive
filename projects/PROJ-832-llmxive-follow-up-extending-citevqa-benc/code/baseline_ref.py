"""
Baseline Reference Module for CiteVQA SAA Scalar.

This module provides functions to load and validate the immutable
baseline SAA (Strict Attributed Accuracy) scalar derived from the
CiteVQA paper (Chen et al., 2024).

It ensures the baseline data adheres to the expected schema:
{
    "baseline_saa": <float>,
    "source": <string>
}
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_config_dict

# Configure logging
logger = logging.getLogger(__name__)


class BaselineSchemaError(Exception):
    """Raised when the baseline JSON does not match the required schema."""
    pass


def get_baseline_path() -> Path:
    """
    Returns the path to the baseline SAA JSON file.
    Uses the project root from config or defaults to 'data/baseline_saa.json'.
    """
    config = get_config_dict()
    base_dir = config.get("project_root", Path.cwd())
    baseline_file = Path(base_dir) / "data" / "baseline_saa.json"
    return baseline_file


def load_baseline_saa() -> Dict[str, Any]:
    """
    Loads the baseline SAA scalar and source metadata from disk.

    Returns:
        Dict containing 'baseline_saa' (float) and 'source' (str).

    Raises:
        FileNotFoundError: If the baseline file does not exist.
        BaselineSchemaError: If the file content is malformed or missing required keys.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = get_baseline_path()

    if not path.exists():
        logger.error(f"Baseline file not found at: {path}")
        raise FileNotFoundError(f"Baseline file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in baseline file {path}: {e}")
        raise

    # Validate schema
    required_keys = {"baseline_saa", "source"}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - set(data.keys())
        msg = f"Baseline JSON missing required keys: {missing}. Found: {list(data.keys())}"
        logger.error(msg)
        raise BaselineSchemaError(msg)

    if not isinstance(data["baseline_saa"], (int, float)):
        msg = f"baseline_saa must be a number, got {type(data['baseline_saa'])}"
        logger.error(msg)
        raise BaselineSchemaError(msg)

    if not isinstance(data["source"], str):
        msg = f"source must be a string, got {type(data['source'])}"
        logger.error(msg)
        raise BaselineSchemaError(msg)

    logger.info(f"Loaded baseline SAA: {data['baseline_saa']} from {data['source']}")
    return data


def get_baseline_value() -> float:
    """
    Convenience function to retrieve just the baseline SAA scalar value.

    Returns:
        float: The baseline SAA value.

    Raises:
        FileNotFoundError, BaselineSchemaError, json.JSONDecodeError:
            Propagated from load_baseline_saa().
    """
    data = load_baseline_saa()
    return float(data["baseline_saa"])


def validate_baseline_consistency(new_value: float, tolerance: float = 0.001) -> bool:
    """
    Checks if a new computed value is consistent with the stored baseline.
    This is useful for sanity checks before running statistical tests.

    Args:
        new_value: A computed SAA value to compare against the baseline.
        tolerance: Allowed difference for equality check.

    Returns:
        bool: True if |new_value - baseline| <= tolerance.
    """
    try:
        baseline = get_baseline_value()
        return abs(new_value - baseline) <= tolerance
    except Exception as e:
        logger.warning(f"Could not validate consistency: {e}")
        return False


def main():
    """
    CLI entry point to demonstrate loading the baseline.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        data = load_baseline_saa()
        print(f"Baseline SAA: {data['baseline_saa']}")
        print(f"Source: {data['source']}")
    except Exception as e:
        print(f"Error loading baseline: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
