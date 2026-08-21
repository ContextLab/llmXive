"""
Unity Verification Module for PROJ-134.

This module verifies the simulation's fidelity to the actual Unity environment
by validating blend-shape parameters against the reference configuration file
(data/config/unity_blend_shapes.yaml).

It explicitly replaces the spec's assumption of a runnable Unity environment
with a mock configuration validation, as authorized by the "Staged Implementation
Authorization" in plan.md.

The script validates:
1. Range constraints (0.0 <= param <= 1.0) for all blend shapes.
2. Salience level consistency (low/high) in the YAML.
3. Key existence for all expected blend shape parameters.
4. Metadata integrity (counts match actual entries).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.config import get_path, validate_data_mode
from code.utils.logging import get_logger

# Constants
REFERENCE_CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
VERIFICATION_REPORT_PATH = "state/unity_verification_report.json"
VALIDATION_STATUS_KEY = "validation_status"

# Expected blend shape parameters based on the spec and YAML structure
EXPECTED_BLEND_SHAPE_KEYS = [
    "jawOpen",
    "browLower",
    "eyeBlink",
    "mouthCornerPull",
    "noseSneer"
]

EXPECTED_SALENCE_LEVELS = ["low", "high"]
PARAM_MIN = 0.0
PARAM_MAX = 1.0


def load_reference_config(config_path: str) -> Dict[str, Any]:
    """
    Load the Unity blend shape reference configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the file is not valid YAML or is missing required sections.
    """
    full_path = get_path(config_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Reference configuration not found at {full_path}")

    import yaml
    with open(full_path, 'r') as f:
        config = yaml.safe_load(f)

    if 'mappings' not in config:
        raise ValueError("Configuration missing 'mappings' section")
    if 'metadata' not in config:
        raise ValueError("Configuration missing 'metadata' section")

    return config


def validate_blend_shape_ranges(blend_shape_params: Dict[str, float], story_id: str) -> List[str]:
    """
    Validate that all blend shape parameters are within the valid range [0.0, 1.0].

    Args:
        blend_shape_params: Dictionary of blend shape names to values.
        story_id: Identifier for the story being validated (for logging).

    Returns:
        List of validation error messages. Empty if valid.
    """
    errors = []
    for key, value in blend_shape_params.items():
        if not isinstance(value, (int, float)):
            errors.append(f"Story {story_id}: Parameter '{key}' is not numeric (got {type(value).__name__})")
            continue

        if value < PARAM_MIN or value > PARAM_MAX:
            errors.append(
                f"Story {story_id}: Parameter '{key}' value {value} is out of range "
                f"[{PARAM_MIN}, {PARAM_MAX}]"
            )
    return errors


def validate_salience_mapping(mappings: Dict[str, Any]) -> List[str]:
    """
    Validate that salience levels are consistent and valid.

    Args:
        mappings: The 'mappings' section from the config.

    Returns:
        List of validation error messages.
    """
    errors = []
    for story_id, data in mappings.items():
        salience = data.get('salience_level')
        if salience not in EXPECTED_SALENCE_LEVELS:
            errors.append(
                f"Story {story_id}: Invalid salience level '{salience}'. "
                f"Expected one of {EXPECTED_SALENCE_LEVELS}"
            )
    return errors


def validate_blend_shape_keys(mappings: Dict[str, Any]) -> List[str]:
    """
    Validate that all expected blend shape keys are present in every story mapping.

    Args:
        mappings: The 'mappings' section from the config.

    Returns:
        List of validation error messages.
    """
    errors = []
    for story_id, data in mappings.items():
        params = data.get('blend_shape_params', {})
        missing_keys = set(EXPECTED_BLEND_SHAPE_KEYS) - set(params.keys())
        if missing_keys:
            errors.append(
                f"Story {story_id}: Missing blend shape parameters: {missing_keys}"
            )
    return errors


def validate_metadata_consistency(config: Dict[str, Any]) -> List[str]:
    """
    Validate that metadata counts match the actual number of entries in mappings.

    Args:
        config: The full configuration dictionary.

    Returns:
        List of validation error messages.
    """
    errors = []
    metadata = config.get('metadata', {})
    mappings = config.get('mappings', {})

    actual_total = len(mappings)
    actual_high = sum(1 for m in mappings.values() if m.get('salience_level') == 'high')
    actual_low = sum(1 for m in mappings.values() if m.get('salience_level') == 'low')

    expected_total = metadata.get('total_stories')
    expected_high = metadata.get('high_salience_count')
    expected_low = metadata.get('low_salience_count')

    if expected_total is not None and actual_total != expected_total:
        errors.append(
            f"Metadata mismatch: total_stories declared as {expected_total}, "
            f"but found {actual_total} in mappings"
        )

    if expected_high is not None and actual_high != expected_high:
        errors.append(
            f"Metadata mismatch: high_salience_count declared as {expected_high}, "
            f"but found {actual_high} in mappings"
        )

    if expected_low is not None and actual_low != expected_low:
        errors.append(
            f"Metadata mismatch: low_salience_count declared as {expected_low}, "
            f"but found {actual_low} in mappings"
        )

    return errors


def verify_simulation_fidelity(config_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Main verification function that runs all validation checks against the config.

    This function verifies that the mock configuration in `data/config/unity_blend_shapes.yaml`
    is structurally sound, within valid ranges, and consistent with its own metadata.
    This ensures the simulation logic (T016) has a reproducible, valid ground truth.

    Args:
        config_path: Path to the reference YAML configuration.

    Returns:
        A tuple of (is_valid, report_dict).
        is_valid: True if all checks pass.
        report_dict: Detailed results of the verification.
    """
    logger = get_logger("unity_verification")
    logger.info(f"Starting Unity simulation fidelity verification using {config_path}")

    try:
        config = load_reference_config(config_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load configuration: {e}")
        return False, {
            "status": "failed",
            "error": str(e),
            "checks_performed": ["load_config"],
            "checks_passed": 0,
            "total_checks": 1
        }

    checks = [
        ("salience_mapping", validate_salience_mapping, config['mappings']),
        ("blend_shape_keys", validate_blend_shape_keys, config['mappings']),
        ("metadata_consistency", validate_metadata_consistency, config),
    ]

    all_errors = []
    checks_passed = 0
    total_checks = len(checks)

    # Run structural checks
    for check_name, check_func, data in checks:
        errors = check_func(data)
        if errors:
            all_errors.extend(errors)
            logger.warning(f"Check '{check_name}' failed: {len(errors)} errors")
        else:
            checks_passed += 1
            logger.info(f"Check '{check_name}' passed")

    # Run per-story range checks
    range_errors = []
    for story_id, data in config['mappings'].items():
        params = data.get('blend_shape_params', {})
        errors = validate_blend_shape_ranges(params, story_id)
        range_errors.extend(errors)

    if range_errors:
        all_errors.extend(range_errors)
        logger.warning(f"Range validation failed: {len(range_errors)} errors")
    else:
        checks_passed += 1
        logger.info("Check 'blend_shape_ranges' passed")
        total_checks += 1

    is_valid = len(all_errors) == 0
    status = "PASSED" if is_valid else "FAILED"

    report = {
        "status": status,
        "is_valid": is_valid,
        "config_source": config_path,
        "checks_performed": [c[0] for c in checks] + ["blend_shape_ranges"],
        "checks_passed": checks_passed,
        "total_checks": total_checks,
        "errors": all_errors,
        "summary": {
            "total_stories": len(config['mappings']),
            "high_salience": sum(1 for m in config['mappings'].values() if m['salience_level'] == 'high'),
            "low_salience": sum(1 for m in config['mappings'].values() if m['salience_level'] == 'low')
        }
    }

    if is_valid:
        logger.info(f"Verification PASSED: Simulation configuration is valid.")
    else:
        logger.error(f"Verification FAILED: {len(all_errors)} errors found.")

    return is_valid, report


def create_reference_config(output_path: str) -> None:
    """
    (Optional) Create a reference configuration if one does not exist.
    This is primarily for bootstrapping, though the task assumes the file exists.
    """
    import yaml
    from datetime import datetime

    config = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "mappings": {
            "story_001": {
                "salience_level": "high",
                "blend_shape_params": {
                    "jawOpen": 0.85,
                    "browLower": 0.90,
                    "eyeBlink": 0.20,
                    "mouthCornerPull": 0.10,
                    "noseSneer": 0.75
                }
            },
            "story_006": {
                "salience_level": "low",
                "blend_shape_params": {
                    "jawOpen": 0.10,
                    "browLower": 0.15,
                    "eyeBlink": 0.50,
                    "mouthCornerPull": 0.20,
                    "noseSneer": 0.05
                }
            }
        },
        "metadata": {
            "total_stories": 2,
            "high_salience_count": 1,
            "low_salience_count": 1,
            "parameter_range": {"min": 0.0, "max": 1.0},
            "validation_status": "verified"
        }
    }

    full_path = get_path(output_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def save_verification_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the verification report to a JSON file.

    Args:
        report: The report dictionary.
        output_path: Path to the output JSON file.
    """
    full_path = get_path(output_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        json.dump(report, f, indent=2)
    logging.getLogger("unity_verification").info(f"Verification report saved to {full_path}")


def main():
    """
    Main entry point for the Unity verification script.
    """
    # Ensure data modes are validated (though this task is config-focused)
    try:
        validate_data_mode()
    except Exception as e:
        # Non-fatal for this specific check, but log it
        logging.warning(f"Data mode validation warning: {e}")

    config_path = REFERENCE_CONFIG_PATH
    report_path = VERIFICATION_REPORT_PATH

    is_valid, report = verify_simulation_fidelity(config_path)
    save_verification_report(report, report_path)

    # Exit with error code if verification failed
    if not is_valid:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()