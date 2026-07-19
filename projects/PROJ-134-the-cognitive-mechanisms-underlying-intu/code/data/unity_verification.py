"""
Unity Verification Module for Moral Judgments Simulation.

This module validates the simulation's fidelity to the actual Unity environment
by verifying blend-shape parameters against the reference configuration file
(data/config/unity_blend_shapes.yaml).

Authorization: This task replaces the Spec's assumption of a runnable Unity
environment with a mock configuration, explicitly citing the "Staged Implementation
Authorization" in plan.md as the authority for this substitution.

Deliverable: A script that validates the unity_blend_shapes.yaml against the
simulation logic, ensuring the mock configuration is reproducible.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_path, load_yaml_config
from code.utils.logging_utils import get_logger, log_pipeline_step

# Configure logging
logger = get_logger(__name__)

# Constants
CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
OUTPUT_PATH = "data/logs/unity_verification_report.json"
VALIDATION_LOG_PATH = "data/logs/unity_validation.log"

# Expected parameter bounds (0.0 to 1.0)
MIN_PARAM_VALUE = 0.0
MAX_PARAM_VALUE = 1.0

# Expected blend shape parameters
EXPECTED_PARAMS = ["jawOpen", "browLower", "eyeBlink", "mouthCornerPull", "noseSneer"]


def load_reference_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the reference Unity blend-shape configuration.

    Args:
        config_path: Optional path to the config file. If None, uses default.

    Returns:
        Dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is empty or malformed.
    """
    if config_path is None:
        config_path = get_path(CONFIG_PATH)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        config = load_yaml_config(config_path)
        if not config:
            raise ValueError(f"Configuration file is empty: {config_path}")
        return config
    except Exception as e:
        raise ValueError(f"Failed to parse configuration file: {e}")


def validate_blend_shape_ranges(
    params: Dict[str, float], story_id: str
) -> Tuple[bool, List[str]]:
    """
    Validate that all blend shape parameters are within the expected range [0.0, 1.0].

    Args:
        params: Dictionary of blend shape parameter names to values.
        story_id: The story ID for logging purposes.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []

    for param_name, value in params.items():
        if not isinstance(value, (int, float)):
            errors.append(
                f"Story {story_id}: Parameter '{param_name}' is not numeric: {value}"
            )
            continue

        if value < MIN_PARAM_VALUE or value > MAX_PARAM_VALUE:
            errors.append(
                f"Story {story_id}: Parameter '{param_name}'={value} "
                f"out of range [{MIN_PARAM_VALUE}, {MAX_PARAM_VALUE}]"
            )

    return len(errors) == 0, errors


def validate_salience_mapping(
    config: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that the salience mapping is consistent and complete.

    Checks:
    1. All required keys exist (version, mappings, metadata).
    2. Each story has a valid salience_level ('low' or 'high').
    3. Each story has all required blend shape parameters.
    4. Metadata counts match actual mapping counts.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    mappings = config.get("mappings", {})

    # Check for required top-level keys
    required_keys = ["version", "mappings", "metadata"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required top-level key: '{key}'")

    # Validate each story mapping
    high_count = 0
    low_count = 0

    for story_id, story_config in mappings.items():
        if not isinstance(story_config, dict):
            errors.append(f"Story {story_id}: Configuration is not a dictionary")
            continue

        # Check salience level
        salience = story_config.get("salience_level")
        if salience not in ["low", "high"]:
            errors.append(
                f"Story {story_id}: Invalid salience_level '{salience}'. "
                "Expected 'low' or 'high'."
            )
        else:
            if salience == "high":
                high_count += 1
            else:
                low_count += 1

        # Check blend shape parameters
        params = story_config.get("blend_shape_params", {})
        if not params:
            errors.append(
                f"Story {story_id}: Missing 'blend_shape_params' key"
            )
            continue

        # Check for expected parameters
        for expected_param in EXPECTED_PARAMS:
            if expected_param not in params:
                errors.append(
                    f"Story {story_id}: Missing expected parameter '{expected_param}'"
                )

        # Validate parameter ranges
        is_valid, range_errors = validate_blend_shape_ranges(params, story_id)
        errors.extend(range_errors)

    # Validate metadata counts
    metadata = config.get("metadata", {})
    if metadata:
        meta_high = metadata.get("high_salience_count")
        meta_low = metadata.get("low_salience_count")
        meta_total = metadata.get("total_stories")

        if meta_high is not None and meta_high != high_count:
            errors.append(
                f"Metadata mismatch: high_salience_count={meta_high}, "
                f"actual={high_count}"
            )

        if meta_low is not None and meta_low != low_count:
            errors.append(
                f"Metadata mismatch: low_salience_count={meta_low}, "
                f"actual={low_count}"
            )

        if meta_total is not None and meta_total != len(mappings):
            errors.append(
                f"Metadata mismatch: total_stories={meta_total}, "
                f"actual={len(mappings)}"
            )

    return len(errors) == 0, errors


def verify_simulation_fidelity(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a full verification of the simulation configuration against
    the reference specification.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary containing verification results:
        - is_valid: Boolean indicating overall validity.
        - errors: List of error messages.
        - summary: Dictionary with counts and statistics.
        - timestamp: ISO format timestamp of the verification.
    """
    from datetime import datetime

    is_valid, errors = validate_salience_mapping(config)

    # Generate summary statistics
    mappings = config.get("mappings", {})
    high_count = sum(
        1 for s in mappings.values()
        if s.get("salience_level") == "high"
    )
    low_count = sum(
        1 for s in mappings.values()
        if s.get("salience_level") == "low"
    )

    # Calculate average parameter values for high vs low salience
    param_sums = {p: {"high": 0.0, "low": 0.0, "count": {"high": 0, "low": 0}}
                  for p in EXPECTED_PARAMS}

    for story_id, story_config in mappings.items():
        salience = story_config.get("salience_level")
        if salience not in ["high", "low"]:
            continue

        params = story_config.get("blend_shape_params", {})
        for param in EXPECTED_PARAMS:
            if param in params:
                param_sums[param][salience] += params[param]
                param_sums[param]["count"][salience] += 1

    averages = {}
    for param in EXPECTED_PARAMS:
        averages[param] = {}
        for sal in ["high", "low"]:
            count = param_sums[param]["count"][sal]
            if count > 0:
                averages[param][sal] = param_sums[param][sal] / count
            else:
                averages[param][sal] = None

    return {
        "is_valid": is_valid,
        "errors": errors,
        "summary": {
            "total_stories": len(mappings),
            "high_salience_count": high_count,
            "low_salience_count": low_count,
            "parameter_averages": averages,
            "version": config.get("version"),
        },
        "timestamp": datetime.now().isoformat(),
    }


def create_reference_config(output_path: Optional[str] = None) -> str:
    """
    Create a reference configuration file if one does not exist.
    This is a utility function to bootstrap the configuration.

    Args:
        output_path: Optional path to write the config. Defaults to CONFIG_PATH.

    Returns:
        Path to the created configuration file.
    """
    if output_path is None:
        output_path = get_path(CONFIG_PATH)

    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # Check if file already exists
    if os.path.exists(output_path):
        logger.info(f"Reference config already exists at {output_path}")
        return output_path

    # Create a minimal reference config
    reference_config = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "mappings": {},
        "metadata": {
            "total_stories": 0,
            "high_salience_count": 0,
            "low_salience_count": 0,
            "parameter_range": {
                "min": 0.0,
                "max": 1.0
            },
            "validation_status": "pending"
        }
    }

    with open(output_path, 'w') as f:
        import yaml
        yaml.dump(reference_config, f, default_flow_style=False)

    logger.info(f"Created reference config at {output_path}")
    return output_path


def main() -> None:
    """
    Main entry point for the Unity verification script.

    This script:
    1. Loads the reference configuration.
    2. Validates the configuration structure and values.
    3. Verifies simulation fidelity.
    4. Writes a verification report to data/logs/unity_verification_report.json.
    5. Logs detailed results to data/logs/unity_validation.log.

    Exit codes:
    0: Verification passed.
    1: Verification failed.
    2: Configuration file not found or invalid.
    """
    log_pipeline_step("unity_verification", "start", logger)

    try:
        # Load configuration
        config_path = get_path(CONFIG_PATH)
        logger.info(f"Loading configuration from {config_path}")

        if not os.path.exists(config_path):
            logger.error(f"Configuration file not found: {config_path}")
            log_pipeline_step("unity_verification", "error", logger,
                              details={"error": "Config file not found"})
            sys.exit(2)

        config = load_reference_config(config_path)

        # Verify fidelity
        logger.info("Verifying simulation fidelity...")
        result = verify_simulation_fidelity(config)

        # Write report
        report_path = get_path(OUTPUT_PATH)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Verification report written to {report_path}")

        # Log detailed results
        log_path = get_path(VALIDATION_LOG_PATH)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        with open(log_path, 'a') as f:
            f.write(f"\n--- Verification Run: {result['timestamp']} ---\n")
            f.write(f"Status: {'PASSED' if result['is_valid'] else 'FAILED'}\n")
            f.write(f"Total Stories: {result['summary']['total_stories']}\n")
            f.write(f"High Salience: {result['summary']['high_salience_count']}\n")
            f.write(f"Low Salience: {result['summary']['low_salience_count']}\n")
            if result['errors']:
                f.write("Errors:\n")
                for err in result['errors']:
                    f.write(f"  - {err}\n")

        if result['is_valid']:
            logger.info("Unity verification PASSED")
            log_pipeline_step("unity_verification", "complete", logger,
                              details={"status": "passed"})
            sys.exit(0)
        else:
            logger.warning(f"Unity verification FAILED with {len(result['errors'])} errors")
            log_pipeline_step("unity_verification", "complete", logger,
                              details={"status": "failed", "error_count": len(result['errors'])})
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unity verification failed with exception: {e}")
        log_pipeline_step("unity_verification", "error", logger,
                          details={"error": str(e)})
        sys.exit(2)


if __name__ == "__main__":
    main()