"""
Structured logging utilities for environmental parameters.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

class EnvironmentalFormatter(logging.Formatter):
    """Custom formatter for environmental parameter logs."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "component": getattr(record, 'component', 'unknown'),
            "action": getattr(record, 'action', 'unknown'),
            "message": record.getMessage(),
        }
        
        # Attach extra environmental fields if present
        if hasattr(record, 'env_params'):
            log_data['env_params'] = record.env_params
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration with environmental formatting.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('llmXive')
    logger.setLevel(getattr(logging, log_level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(EnvironmentalFormatter())
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(EnvironmentalFormatter())
        logger.addHandler(file_handler)

    return logger


def log_environmental_params(
    logger: logging.Logger,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    dielectric_constant: Optional[float] = None,
    solvent_name: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log environmental parameters in a structured format.

    Args:
        logger: Logger instance to use
        temperature: Temperature in Celsius
        humidity: Relative humidity in percent
        dielectric_constant: Dielectric constant of the solvent
        solvent_name: Name of the solvent
        **kwargs: Additional parameters to log
    """
    env_params = {}
    if temperature is not None:
        env_params['temperature_c'] = temperature
    if humidity is not None:
        env_params['humidity_percent'] = humidity
    if dielectric_constant is not None:
        env_params['dielectric_constant'] = dielectric_constant
    if solvent_name is not None:
        env_params['solvent_name'] = solvent_name
    
    env_params.update(kwargs)

    logger.info(
        "Environmental parameters recorded",
        extra={'env_params': env_params}
    )


def log_compliance_check(
    component: str,
    action: str,
    details: str
) -> None:
    """
    Log a compliance check event.

    Args:
        component: The component performing the check
        action: The action taken (e.g., 'fetch', 'validate', 'skip')
        details: Detailed message about the compliance check
    """
    logger = logging.getLogger('llmXive')
    logger.info(
        f"Compliance check: {action}",
        extra={
            'component': component,
            'action': action,
            'details': details
        }
    )
