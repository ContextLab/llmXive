"""
Logging infrastructure for the project.

Provides configured loggers and helper functions for logging exclusions,
VR mapping, and pipeline steps.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path

# Ensure log directories exist
log_dir = get_path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.

    Args:
        name: Name of the module (usually __name__)

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Create file handler for general logs
    log_file = get_path("data/logs", "pipeline.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def get_log_path(filename: str) -> Path:
    """
    Get the full path for a log file.

    Args:
        filename: Name of the log file.

    Returns:
        Path object for the log file.
    """
    return get_path("data/logs", filename)

def get_exclusion_log_path() -> Path:
    """
    Get the path for the exclusion log file.

    Returns:
        Path object for the exclusion log file.
    """
    return get_path("data/logs", "exclusion.log")

def get_vr_mapping_log_path() -> Path:
    """
    Get the path for the VR mapping log file.

    Returns:
        Path object for the VR mapping log file.
    """
    return get_path("data/logs", "vr_mapping.log")

def log_exclusion(field: str, value: str, reason: str, logger: Optional[logging.Logger] = None):
    """
    Log an exclusion reason to the exclusion log file.

    Args:
        field: The field that caused the exclusion.
        value: The value that was excluded.
        reason: The reason for exclusion.
        logger: Optional logger instance.
    """
    exclusion_path = get_exclusion_log_path()
    timestamp = datetime.now().isoformat()

    log_entry = f"{timestamp}|{field}|{value}|{reason}\n"

    # Write directly to file
    with open(exclusion_path, 'a') as f:
        f.write(log_entry)

    if logger:
        logger.warning(f"Exclusion logged: {field}={value} - {reason}")

def log_vr_mapping(story_id: str, salience_level: str, blend_shape_params: Dict[str, float], logger: Optional[logging.Logger] = None):
    """
    Log VR mapping information to the VR mapping log file.

    Args:
        story_id: The ID of the story.
        salience_level: The assigned salience level ('low' or 'high').
        blend_shape_params: Dictionary of blend shape parameters.
        logger: Optional logger instance.
    """
    vr_mapping_path = get_vr_mapping_log_path()
    timestamp = datetime.now().isoformat()

    # Convert params to JSON string for logging
    import json
    params_str = json.dumps(blend_shape_params)

    log_entry = f"{story_id},{salience_level},{params_str}\n"

    # Write directly to file
    with open(vr_mapping_path, 'a') as f:
        f.write(log_entry)

    if logger:
        logger.debug(f"VR mapping logged: story_id={story_id}, salience={salience_level}")

def log_pipeline_step(step_name: str, details: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
    """
    Log a pipeline step with optional details.

    Args:
        step_name: Name of the pipeline step.
        details: Optional dictionary of step details.
        logger: Optional logger instance.
    """
    if logger:
        msg = f"Pipeline Step: {step_name}"
        if details:
            msg += f" | Details: {details}"
        logger.info(msg)

def main():
    """
    Test the logging infrastructure.
    """
    logger = get_logger("logging_test")
    logger.info("Logging infrastructure test started.")

    # Test exclusion logging
    log_exclusion("test_field", "test_value", "Test reason", logger)

    # Test VR mapping logging
    log_vr_mapping("story_001", "high", {"blend_0": 0.5, "blend_1": 0.8}, logger)

    # Test pipeline step logging
    log_pipeline_step("test_step", {"status": "success"}, logger)

    logger.info("Logging infrastructure test completed.")

if __name__ == "__main__":
    main()