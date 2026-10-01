"""
Module: define_lift.py
Purpose: Define the '[deferred] lift' threshold value in code/config.py based on power analysis results.
If the power analysis indicates insufficient data, write a placeholder string 'DEFERRED' to handle the state deterministically.
"""

import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from project modules
from config import get_project_root, get_path_absolute, ensure_directory, get_config_dict
from logging_config import get_logger, log_event
from analysis.power import run_power_analysis

# Configure logger
logger = get_logger(__name__)

# Constants
LIFT_THRESHOLD_KEY = "lift_threshold"
DEFERRED_VALUE = "DEFERRED"
DEFAULT_LIFT_THRESHOLD = 0.05  # Default 5% lift if power analysis suggests data is sufficient but no specific value found
POWER_ANALYSIS_FILE = "data/validation/power_analysis_results.json"


def load_power_analysis_results() -> Optional[Dict[str, Any]]:
    """
    Load the power analysis results from the validation directory.
    Returns None if the file does not exist or is invalid.
    """
    project_root = get_project_root()
    power_analysis_path = get_path_absolute(project_root, POWER_ANALYSIS_FILE)

    if not os.path.exists(power_analysis_path):
        logger.warning(f"Power analysis results file not found: {power_analysis_path}")
        return None

    try:
        with open(power_analysis_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Successfully loaded power analysis results from {power_analysis_path}")
            return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load or parse power analysis results: {e}")
        return None


def calculate_lift_threshold(power_results: Optional[Dict[str, Any]]) -> str:
    """
    Determine the lift threshold value based on power analysis results.
    
    Logic:
    1. If power analysis results are missing, return 'DEFERRED'.
    2. If power analysis indicates insufficient data (e.g., 'sufficient_data' is False), return 'DEFERRED'.
    3. If power analysis provides a specific 'lift_threshold' value, use it.
    4. Otherwise, use the DEFAULT_LIFT_THRESHOLD.
    
    Returns:
        str: The determined lift threshold value (as a string) or 'DEFERRED'.
    """
    if power_results is None:
        logger.info("Power analysis results are missing. Setting lift threshold to 'DEFERRED'.")
        return DEFERRED_VALUE

    is_sufficient = power_results.get("sufficient_data", False)
    if not is_sufficient:
        logger.info("Power analysis indicates insufficient data. Setting lift threshold to 'DEFERRED'.")
        return DEFERRED_VALUE

    # Check if a specific lift threshold was calculated
    calculated_lift = power_results.get("lift_threshold")
    if calculated_lift is not None:
        logger.info(f"Using calculated lift threshold from power analysis: {calculated_lift}")
        return str(calculated_lift)

    logger.info(f"No specific lift threshold found in power analysis. Using default: {DEFAULT_LIFT_THRESHOLD}")
    return str(DEFAULT_LIFT_THRESHOLD)


def update_config_with_lift_threshold(lift_threshold_value: str) -> bool:
    """
    Update the code/config.py file to include the defined lift threshold value.
    
    Args:
        lift_threshold_value: The string value to set for the lift threshold.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    project_root = get_project_root()
    config_path = get_path_absolute(project_root, "code/config.py")
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Define the new configuration line to add/update
        new_config_line = f'    "{LIFT_THRESHOLD_KEY}": "{lift_threshold_value}",'

        # Check if the key already exists in the config dict
        # We look for the pattern in the get_config_dict function
        if f'"{LIFT_THRESHOLD_KEY}"' in content:
            logger.info(f"Found existing '{LIFT_THRESHOLD_KEY}' in config. Updating value.")
            # Simple replacement for the value part of the line
            import re
            # Pattern to match the line with the key and capture the value
            pattern = re.compile(rf'(\s*"{LIFT_THRESHOLD_KEY}":\s*")[^"]*(",)', re.MULTILINE)
            replacement = rf'\g<1>{lift_threshold_value}\g<2>'
            updated_content = pattern.sub(replacement, content)
        else:
            logger.info(f"'{LIFT_THRESHOLD_KEY}' not found in config. Adding new entry.")
            # Find the get_config_dict function and insert the new line before the closing brace
            # We look for the return statement or the closing brace of the dict
            if "return config_dict" in content:
                # Insert before the return statement
                lines = content.split('\n')
                new_lines = []
                inserted = False
                for line in lines:
                    if "return config_dict" in line and not inserted:
                        new_lines.append(new_config_line)
                        inserted = True
                    new_lines.append(line)
                updated_content = '\n'.join(new_lines)
            else:
                logger.error("Could not find 'return config_dict' in config.py. Cannot insert new key.")
                return False

        # Write the updated content back to the file
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"Successfully updated {config_path} with lift_threshold = {lift_threshold_value}")
        return True

    except IOError as e:
        logger.error(f"Failed to update config file: {e}")
        return False


def main():
    """
    Main function to define and set the lift threshold.
    """
    logger.info("Starting lift threshold definition process.")
    
    # Load power analysis results
    power_results = load_power_analysis_results()
    
    # Calculate lift threshold
    lift_threshold_value = calculate_lift_threshold(power_results)
    
    # Update config file
    success = update_config_with_lift_threshold(lift_threshold_value)
    
    if success:
        logger.info(f"Lift threshold successfully set to '{lift_threshold_value}' in code/config.py")
        log_event("lift_threshold_defined", {"value": lift_threshold_value, "source": "power_analysis"})
    else:
        logger.error("Failed to update lift threshold in config file.")
        log_event("lift_threshold_definition_failed", {"reason": "config_update_failed"})
        sys.exit(1)


if __name__ == "__main__":
    main()