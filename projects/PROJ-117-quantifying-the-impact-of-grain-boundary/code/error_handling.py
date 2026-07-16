"""
Error handling module for the grain boundary diffusivity project.
Provides custom exceptions and exit logic for data insufficiency.
"""
import logging
import sys
from typing import Optional, List

logger = logging.getLogger(__name__)

class DataInsufficiencyError(Exception):
    """Custom exception for data insufficiency."""
    pass

def check_data_sufficiency(retrieved: int, required: int, missing_features: Optional[List[str]] = None) -> bool:
    """
    Check if the retrieved data meets the minimum requirement.
    
    Args:
        retrieved: Number of records retrieved.
        required: Minimum required records.
        missing_features: List of missing feature names.
        
    Returns:
        True if sufficient, False otherwise.
    """
    if retrieved < required:
        feature_msg = ""
        if missing_features:
            feature_msg = f". Missing features: {', '.join(missing_features)}"
        logger.error(f"Data Insufficiency: Retrieved {retrieved}, Valid {retrieved}, Required {required}{feature_msg}")
        return False
    return True

def exit_on_insufficiency(retrieved: int, required: int, missing_features: Optional[List[str]] = None) -> None:
    """
    Log the insufficiency error and exit with code 1.
    
    Args:
        retrieved: Number of records retrieved.
        required: Minimum required records.
        missing_features: List of missing feature names.
    """
    feature_msg = ""
    if missing_features:
        feature_msg = f". Missing features: {', '.join(missing_features)}"
    error_msg = f"Data Insufficiency: Retrieved {retrieved}, Valid {retrieved}, Required {required}{feature_msg}"
    logger.error(error_msg)
    raise DataInsufficiencyError(error_msg)