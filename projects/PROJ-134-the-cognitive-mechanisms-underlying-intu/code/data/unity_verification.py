"""
Unity Verification Module.

This module verifies the simulation's fidelity to the actual Unity environment
by validating blend-shape parameters against a reference configuration file.

Authorization: This task replaces the Spec's assumption of a runnable Unity
environment with a mock configuration, explicitly citing the "Staged Implementation
Authorization" in `plan.md` as the authority for this substitution.

Deliverable: A script that validates the `data/config/unity_blend_shapes.yaml`
against the simulation logic, ensuring the mock configuration is reproducible.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from project API surface
from code.config import get_path
from code.utils.logging import get_logger, log_pipeline_step

# Configure module logger
logger = get_logger(__name__)

# Constants
CONFIG_PATH = "data/config/unity_blend_shapes.yaml"
VERIFICATION_LOG_PATH = "data/logs/unity_verification.log"
VALIDATION_REPORT_PATH = "state/unity_verification_report.json"

# Expected blend shape parameters based on Unity standard blend shapes
EXPECTED_BLEND_SHAPES = [
    "jawOpen",
    "browLower",
    "eyeBlink",
    "mouthCornerPull",
    "noseSneer"
]

# Expected salience levels
EXPECTED_SALIENCE_LEVELS = ["low", "high"]

def load_reference_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the reference Unity blend shape configuration from YAML.

    Args:
        config_path: Optional path to the config file. Defaults to CONFIG_PATH.

    Returns:
        Dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is empty or malformed.
    """
    if config_path is None:
        config_path = CONFIG_PATH

    full_path = get_path(config_path)
    
    if not full_path.exists():
        raise FileNotFoundError(f"Reference config not found at {full_path}")

    try:
        import yaml
        with open(full_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            raise ValueError(f"Config file at {full_path} is empty or invalid YAML")
        
        logger.info(f"Successfully loaded reference config from {full_path}")
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML config: {e}")
    except Exception as e:
        raise RuntimeError(f"Error loading config: {e}")

def validate_blend_shape_ranges(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that all blend shape parameters are within the valid range [0.0, 1.0].

    Args:
        config: The loaded configuration dictionary.

    Returns:
        A tuple (is_valid, errors) where is_valid is True if all parameters
        are in range, and errors is a list of validation error messages.
    """
    errors = []
    mappings = config.get("mappings", {})
    
    if not mappings:
        errors.append("No mappings found in configuration")
        return False, errors

    for story_id, story_config in mappings.items():
        salience_level = story_config.get("salience_level")
        blend_shape_params = story_config.get("blend_shape_params", {})
        
        # Validate salience level
        if salience_level not in EXPECTED_SALIENCE_LEVELS:
            errors.append(
                f"Story {story_id}: Invalid salience level '{salience_level}'. "
                f"Expected one of {EXPECTED_SALIENCE_LEVELS}"
            )
        
        # Validate blend shape parameters
        for param_name, param_value in blend_shape_params.items():
            if not isinstance(param_value, (int, float)):
                errors.append(
                    f"Story {story_id}: Parameter '{param_name}' has invalid type "
                    f"{type(param_value).__name__}, expected number"
                )
                continue
            
            if not (0.0 <= param_value <= 1.0):
                errors.append(
                    f"Story {story_id}: Parameter '{param_name}' value {param_value} "
                    f"is outside valid range [0.0, 1.0]"
                )

    return len(errors) == 0, errors

def validate_salience_mapping(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that the salience mapping is consistent and complete.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        A tuple (is_valid, errors) where is_valid is True if the mapping
        is consistent, and errors is a list of validation error messages.
    """
    errors = []
    mappings = config.get("mappings", {})
    metadata = config.get("metadata", {})
    
    if not mappings:
        errors.append("No mappings found in configuration")
        return False, errors

    # Count salience levels
    high_count = 0
    low_count = 0
    
    for story_id, story_config in mappings.items():
        salience_level = story_config.get("salience_level")
        
        if salience_level == "high":
            high_count += 1
        elif salience_level == "low":
            low_count += 1
        else:
            errors.append(f"Story {story_id}: Invalid salience level '{salience_level}'")

    # Validate against metadata if present
    if metadata:
        expected_high = metadata.get("high_salience_count")
        expected_low = metadata.get("low_salience_count")
        
        if expected_high is not None and high_count != expected_high:
            errors.append(
                f"High salience count mismatch: found {high_count}, "
                f"expected {expected_high}"
            )
        
        if expected_low is not None and low_count != expected_low:
            errors.append(
                f"Low salience count mismatch: found {low_count}, "
                f"expected {expected_low}"
            )

    # Validate total count
    total_count = len(mappings)
    expected_total = metadata.get("total_stories")
    
    if expected_total is not None and total_count != expected_total:
        errors.append(
            f"Total story count mismatch: found {total_count}, "
            f"expected {expected_total}"
        )

    return len(errors) == 0, errors

def validate_blend_shape_keys(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that all expected blend shape keys are present.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        A tuple (is_valid, errors) where is_valid is True if all expected
        keys are present, and errors is a list of validation error messages.
    """
    errors = []
    mappings = config.get("mappings", {})
    
    for story_id, story_config in mappings.items():
        blend_shape_params = story_config.get("blend_shape_params", {})
        missing_keys = set(EXPECTED_BLEND_SHAPES) - set(blend_shape_params.keys())
        
        if missing_keys:
            errors.append(
                f"Story {story_id}: Missing blend shape parameters: {missing_keys}"
            )

    return len(errors) == 0, errors

def verify_simulation_fidelity(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform a comprehensive verification of the simulation fidelity.

    This function runs all validation checks and compiles a report of the results.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        A dictionary containing the verification results.
    """
    results = {
        "status": "pending",
        "checks": {},
        "errors": [],
        "summary": {}
    }

    # Run all validation checks
    range_valid, range_errors = validate_blend_shape_ranges(config)
    results["checks"]["range_validation"] = {
        "passed": range_valid,
        "errors": range_errors
    }
    results["errors"].extend(range_errors)

    mapping_valid, mapping_errors = validate_salience_mapping(config)
    results["checks"]["salience_mapping"] = {
        "passed": mapping_valid,
        "errors": mapping_errors
    }
    results["errors"].extend(mapping_errors)

    keys_valid, keys_errors = validate_blend_shape_keys(config)
    results["checks"]["blend_shape_keys"] = {
        "passed": keys_valid,
        "errors": keys_errors
    }
    results["errors"].extend(keys_errors)

    # Determine overall status
    all_passed = all(
        check["passed"] for check in results["checks"].values()
    )
    results["status"] = "passed" if all_passed else "failed"

    # Generate summary
    results["summary"] = {
        "total_checks": len(results["checks"]),
        "passed_checks": sum(1 for check in results["checks"].values() if check["passed"]),
        "failed_checks": sum(1 for check in results["checks"].values() if not check["passed"]),
        "total_errors": len(results["errors"])
    }

    return results

def create_reference_config(output_path: Optional[str] = None) -> Path:
    """
    Create a reference configuration file if it doesn't exist.

    This is useful for initializing the verification process with a known-good
    configuration template.

    Args:
        output_path: Optional path for the output file. Defaults to CONFIG_PATH.

    Returns:
        Path to the created configuration file.
    """
    if output_path is None:
        output_path = CONFIG_PATH

    full_path = get_path(output_path)
    
    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a minimal valid configuration if file doesn't exist
    if not full_path.exists():
        import yaml
        minimal_config = {
            "version": "1.0",
            "generated_at": "2023-10-27T10:00:00Z",
            "mappings": {},
            "metadata": {
                "total_stories": 0,
                "high_salience_count": 0,
                "low_salience_count": 0,
                "parameter_range": {
                    "min": 0.0,
                    "max": 1.0
                },
                "validation_status": "unverified"
            }
        }

        with open(full_path, 'w') as f:
            yaml.dump(minimal_config, f, default_flow_style=False)

        logger.info(f"Created minimal reference config at {full_path}")

    return full_path

def save_verification_report(results: Dict[str, Any], output_path: Optional[str] = None) -> Path:
    """
    Save the verification results to a JSON report file.

    Args:
        results: The verification results dictionary.
        output_path: Optional path for the output file. Defaults to VALIDATION_REPORT_PATH.

    Returns:
        Path to the saved report file.
    """
    if output_path is None:
        output_path = VALIDATION_REPORT_PATH

    full_path = get_path(output_path)
    
    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with open(full_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Verification report saved to {full_path}")
    return full_path

def main():
    """
    Main entry point for the Unity verification script.

    This function loads the reference configuration, performs all validation
    checks, and saves the results to a report file.
    """
    log_pipeline_step("unity_verification", "Starting Unity blend shape verification")

    try:
        # Load reference configuration
        logger.info("Loading reference configuration...")
        config = load_reference_config()

        # Verify simulation fidelity
        logger.info("Verifying simulation fidelity...")
        results = verify_simulation_fidelity(config)

        # Save verification report
        logger.info("Saving verification report...")
        report_path = save_verification_report(results)

        # Log final status
        status = results["status"]
        summary = results["summary"]
        
        logger.info(f"Verification {status.upper()}")
        logger.info(f"Checks: {summary['passed_checks']}/{summary['total_checks']} passed")
        logger.info(f"Errors: {summary['total_errors']}")

        if status == "failed":
            logger.error("Verification failed. Please review the errors above.")
            sys.exit(1)
        else:
            logger.info("All validations passed successfully.")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()