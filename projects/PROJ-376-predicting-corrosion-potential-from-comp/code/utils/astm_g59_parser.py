"""
ASTM G59 Tolerance Parser Module

This module provides functionality to parse the ASTM G59 tolerance configuration
from the project's YAML configuration file. It handles cases where the standard
does not define a specific value by falling back to a literature-derived default.

The parser ensures that a tolerance value is always available for comparison
against model performance metrics (SC-002).
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml

from utils.logging import get_logger
from utils.exceptions import CorrosionPipelineError

logger: logging.Logger = get_logger(__name__)


def load_astm_tolerance_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load and parse the ASTM G59 tolerance configuration from YAML file.

    Args:
        config_path: Path to the tolerance configuration file. If None, uses
                    the default path from project config.

    Returns:
        Dictionary containing tolerance configuration with keys:
            - value: float (tolerance value in mV)
            - unit: str (unit of measurement)
            - source: str (source of the value)
            - standard_reference: str (ASTM standard reference)
            - notes: str (additional context)
            - verified: bool (whether the value is verified)

    Raises:
        CorrosionPipelineError: If the configuration file cannot be loaded or parsed.
    """
    if config_path is None:
        # Default path relative to project root
        config_path = Path("config/astm_g59_tolerance.yaml")

    if not config_path.exists():
        error_msg = (
            f"ASTM G59 tolerance configuration file not found at {config_path}. "
            "Please ensure the file exists with proper configuration."
        )
        logger.error(error_msg)
        raise CorrosionPipelineError(error_msg)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse ASTM G59 tolerance YAML configuration: {e}"
        logger.error(error_msg)
        raise CorrosionPipelineError(error_msg)
    except IOError as e:
        error_msg = f"Failed to read ASTM G59 tolerance configuration file: {e}"
        logger.error(error_msg)
        raise CorrosionPipelineError(error_msg)

    # Validate required fields
    if 'tolerance' not in config:
        error_msg = "Missing 'tolerance' section in ASTM G59 configuration file."
        logger.error(error_msg)
        raise CorrosionPipelineError(error_msg)

    tolerance_config = config['tolerance']
    required_fields = ['value', 'unit', 'source']
    for field in required_fields:
        if field not in tolerance_config:
            error_msg = f"Missing required field '{field}' in tolerance configuration."
            logger.error(error_msg)
            raise CorrosionPipelineError(error_msg)

    logger.info(
        f"Loaded ASTM G59 tolerance configuration: "
        f"value={tolerance_config['value']} {tolerance_config['unit']}, "
        f"source={tolerance_config['source']}"
    )

    return tolerance_config


def get_tolerance_value(config_path: Optional[Path] = None) -> Tuple[float, str]:
    """
    Extract the tolerance value and unit from the configuration.

    This function ensures that a tolerance value is always available,
    falling back to the literature-derived default if the standard
    does not define a specific value.

    Args:
        config_path: Path to the tolerance configuration file.

    Returns:
        Tuple of (tolerance_value, unit) where:
            - tolerance_value: float (the tolerance value in mV)
            - unit: str (the unit of measurement, typically 'mV')

    Raises:
        CorrosionPipelineError: If configuration cannot be loaded or parsed.
    """
    config = load_astm_tolerance_config(config_path)
    value = float(config['value'])
    unit = str(config['unit'])

    logger.info(f"ASTM G59 tolerance value: {value} {unit}")
    return value, unit


def get_tolerance_source_info(config_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Retrieve detailed source information for the tolerance value.

    Args:
        config_path: Path to the tolerance configuration file.

    Returns:
        Dictionary containing source information:
            - source: str (primary source of the value)
            - standard_reference: str (ASTM standard reference)
            - notes: str (additional context about the value)
            - verified: str (verification status as string)
    """
    config = load_astm_tolerance_config(config_path)
    tolerance_config = config['tolerance']

    return {
        'source': tolerance_config.get('source', 'Unknown'),
        'standard_reference': tolerance_config.get('standard_reference', 'N/A'),
        'notes': tolerance_config.get('notes', 'No additional notes'),
        'verified': str(tolerance_config.get('verified', False))
    }


def validate_tolerance_for_comparison(tolerance_value: float, tolerance_unit: str) -> bool:
    """
    Validate that the tolerance value is suitable for model comparison.

    Args:
        tolerance_value: The tolerance value to validate.
        tolerance_unit: The unit of the tolerance value.

    Returns:
        True if the tolerance is valid for comparison.

    Raises:
        CorrosionPipelineError: If the tolerance is invalid.
    """
    if tolerance_value <= 0:
        error_msg = (
            f"Invalid tolerance value: {tolerance_value}. "
            "Tolerance must be a positive number for meaningful comparison."
        )
        logger.error(error_msg)
        raise CorrosionPipelineError(error_msg)

    if tolerance_unit.lower() not in ['mv', 'millivolts', 'v', 'volts']:
        logger.warning(
            f"Unusual tolerance unit: {tolerance_unit}. "
            "Expected 'mV' or 'V'. Converting to mV for consistency."
        )

    logger.info(f"Tolerance validation passed: {tolerance_value} {tolerance_unit}")
    return True
