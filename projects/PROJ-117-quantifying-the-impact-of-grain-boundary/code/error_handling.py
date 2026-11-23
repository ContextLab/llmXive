"""
Error handling utilities for the grain boundary diffusivity project.
"""
import logging
import sys
from typing import Optional, List

logger = logging.getLogger(__name__)

class DataInsufficiencyError(Exception):
    """Custom exception for data insufficiency errors."""
    pass

def raise_data_insufficiency_error(retrieved: int, required: int, missing_features: List[str]) -> None:
    """
    Raise a DataInsufficiencyError with formatted message.
    
    Args:
        retrieved: Number of records retrieved.
        required: Required number of records.
        missing_features: List of missing feature names.
    """
    error_msg = f"Data Insufficiency: Retrieved {retrieved}, Valid {retrieved}, Required {required}"
    if missing_features:
        error_msg += f". Missing features: {', '.join(missing_features)}"
    
    logger.error(error_msg)
    raise DataInsufficiencyError(error_msg)

def check_data_sufficiency(retrieved: int, required: int, missing_features: Optional[List[str]] = None) -> bool:
    """
    Check if data meets minimum requirements.
    
    Args:
        retrieved: Number of records retrieved.
        required: Required number of records.
        missing_features: List of missing feature names (optional).
    
    Returns:
        True if sufficient, False otherwise.
    """
    if retrieved < required:
        return False
    return True

def exit_on_insufficiency(retrieved: int, required: int, missing_features: Optional[List[str]] = None) -> None:
    """
    Exit the program if data is insufficient.
    
    Args:
        retrieved: Number of records retrieved.
        required: Required number of records.
        missing_features: List of missing feature names (optional).
    """
    if retrieved < required:
        raise_data_insufficiency_error(retrieved, required, missing_features or [])
    else:
        logger.info(f"Data sufficiency check passed: {retrieved} >= {required}")
