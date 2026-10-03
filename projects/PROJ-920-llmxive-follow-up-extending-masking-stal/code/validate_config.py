"""
Configuration Validation Script for llmXive Follow-up Project.

This script validates that simulation_config.json and analysis_config.json
contain all required keys, correct data types, and values within physically
meaningful ranges.

Usage:
    python code/validate_config.py
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SIMULATION_CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "simulation_config.json"
ANALYSIS_CONFIG_PATH = PROJECT_ROOT / "code" / "config" / "analysis_config.json"


# Validation rules for simulation_config.json
SIMULATION_CONFIG_SCHEMA = {
    "alpha": {
        "type": float,
        "min": 0.0,  # Must be positive
        "max": None,
        "required": True,
        "description": "Scaling factor for heuristic solver"
    },
    "threshold": {
        "type": float,
        "min": 0.0,
        "max": 1.0,  # Must be between 0 and 1
        "required": True,
        "description": "Critical density threshold"
    },
    "seed": {
        "type": int,
        "min": None,
        "max": None,
        "required": True,
        "description": "Default random seed"
    },
    "density_levels": {
        "type": list,
        "required": True,
        "description": "List of [low, med, high] target values"
    }
}

# Validation rules for analysis_config.json
ANALYSIS_CONFIG_SCHEMA = {
    "min_samples_per_bin": {
        "type": int,
        "min": 1,  # Must be at least 1
        "max": None,
        "required": True,
        "description": "Minimum samples per bin for statistical validity"
    },
    "splines_df_candidates": {
        "type": list,
        "required": True,
        "description": "List of degrees of freedom candidates for splines"
    },
    "p_value_threshold": {
        "type": float,
        "min": 0.0,
        "max": 1.0,  # Must be between 0 and 1
        "required": True,
        "description": "Threshold for statistical significance"
    }
}


def validate_type(value: Any, expected_type: type, field_name: str) -> Tuple[bool, str]:
    """Validate that a value matches the expected type."""
    if not isinstance(value, expected_type):
        return False, f"Expected type {expected_type.__name__} for '{field_name}', got {type(value).__name__}"
    return True, ""


def validate_range(value: Any, min_val: Optional[float], max_val: Optional[float], field_name: str) -> Tuple[bool, str]:
    """Validate that a numeric value is within the specified range."""
    if min_val is not None and value < min_val:
        return False, f"Value for '{field_name}' ({value}) is below minimum allowed ({min_val})"
    if max_val is not None and value > max_val:
        return False, f"Value for '{field_name}' ({value}) is above maximum allowed ({max_val})"
    return True, ""


def validate_list_elements(value: List, expected_type: type, field_name: str) -> Tuple[bool, str]:
    """Validate that all elements in a list match the expected type."""
    for i, item in enumerate(value):
        if not isinstance(item, expected_type):
            return False, f"Element {i} in '{field_name}' is not of type {expected_type.__name__}"
    return True, ""


def validate_config_file(config_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a configuration file against a schema.

    Args:
        config_path: Path to the configuration file
        schema: Dictionary defining validation rules

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check if file exists
    if not config_path.exists():
        return [f"Configuration file not found: {config_path}"]

    # Load JSON
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in {config_path}: {str(e)}"]
    except Exception as e:
        return [f"Error reading {config_path}: {str(e)}"]

    # Validate each field in the schema
    for field_name, rules in schema.items():
        # Check if field is present
        if field_name not in config:
            if rules.get("required", False):
                errors.append(f"Missing required field: '{field_name}' in {config_path.name}")
            continue

        value = config[field_name]

        # Type validation
        if "type" in rules:
            valid, msg = validate_type(value, rules["type"], field_name)
            if not valid:
                errors.append(msg)
                continue  # Skip range validation if type is wrong

        # Range validation for numeric types
        if rules["type"] in (int, float):
            min_val = rules.get("min")
            max_val = rules.get("max")
            valid, msg = validate_range(value, min_val, max_val, field_name)
            if not valid:
                errors.append(msg)

        # List element validation
        if rules["type"] == list:
            # For density_levels, we expect list of numbers
            if field_name == "density_levels":
                # Check if it's a list of lists (e.g., [[low, med, high]])
                if value and isinstance(value[0], list):
                    for i, sublist in enumerate(value):
                        valid, msg = validate_type(sublist, list, f"{field_name}[{i}]")
                        if not valid:
                            errors.append(msg)
                            continue
                        # Validate each element in the sublist
                        for j, item in enumerate(sublist):
                            if not isinstance(item, (int, float)):
                                errors.append(f"Element [{i}][{j}] in '{field_name}' is not a number")
                elif value:
                    # If it's a flat list, validate elements are numbers
                    valid, msg = validate_list_elements(value, (int, float), field_name)
                    if not valid:
                        errors.append(msg)
            else:
                # For splines_df_candidates, expect list of integers
                valid, msg = validate_list_elements(value, int, field_name)
                if not valid:
                    errors.append(msg)

    return errors


def main():
    """Main entry point for configuration validation."""
    print("Starting configuration validation...")
    all_errors = []

    # Validate simulation_config.json
    print(f"\nValidating {SIMULATION_CONFIG_PATH.name}...")
    sim_errors = validate_config_file(SIMULATION_CONFIG_PATH, SIMULATION_CONFIG_SCHEMA)
    if sim_errors:
        print(f"  ❌ Found {len(sim_errors)} error(s):")
        for error in sim_errors:
            print(f"     - {error}")
        all_errors.extend(sim_errors)
    else:
        print("  ✅ Configuration is valid.")

    # Validate analysis_config.json
    print(f"\nValidating {ANALYSIS_CONFIG_PATH.name}...")
    analysis_errors = validate_config_file(ANALYSIS_CONFIG_PATH, ANALYSIS_CONFIG_SCHEMA)
    if analysis_errors:
        print(f"  ❌ Found {len(analysis_errors)} error(s):")
        for error in analysis_errors:
            print(f"     - {error}")
        all_errors.extend(analysis_errors)
    else:
        print("  ✅ Configuration is valid.")

    # Final result
    print("\n" + "=" * 50)
    if all_errors:
        print(f"❌ VALIDATION FAILED: {len(all_errors)} error(s) found.")
        print("Please fix the configuration files and re-run validation.")
        sys.exit(1)
    else:
        print("✅ VALIDATION PASSED: All configuration files are valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()