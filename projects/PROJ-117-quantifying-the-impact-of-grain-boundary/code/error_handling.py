"""
Error handling infrastructure for the grain boundary diffusivity pipeline.

Provides custom exceptions and utility functions for handling data insufficiency
errors, ensuring proper logging and exit codes when data requirements are not met.
"""

import logging
import sys
from typing import Optional

# Configure module-level logger
logger = logging.getLogger(__name__)


class DataInsufficiencyError(Exception):
    """
    Custom exception raised when the dataset does not meet the minimum record count.
    
    Attributes:
        retrieved_count (int): The number of records actually retrieved.
        required_count (int): The minimum number of records required.
        missing_features (list): Optional list of features that caused insufficiency.
    """
    
    def __init__(
        self,
        retrieved_count: int,
        required_count: int,
        message: Optional[str] = None,
        missing_features: Optional[list] = None
    ):
        self.retrieved_count = retrieved_count
        self.required_count = required_count
        self.missing_features = missing_features or []
        
        if message is None:
            if self.missing_features:
                features_str = ", ".join(self.missing_features)
                message = (
                    f"Data Insufficiency: Retrieved {retrieved_count} records, "
                    f"but {required_count} required. Missing features: {features_str}"
                )
            else:
                message = (
                    f"Data Insufficiency: Retrieved {retrieved_count} records, "
                    f"but {required_count} required."
                )
        
        super().__init__(message)
    
    def __str__(self) -> str:
        return self.args[0]


def check_data_sufficiency(
    current_count: int,
    minimum_required: int,
    missing_features: Optional[list] = None
) -> bool:
    """
    Check if the current record count meets the minimum requirement.
    
    Args:
        current_count: The number of records currently available.
        minimum_required: The minimum number of records required.
        missing_features: Optional list of features causing insufficiency.
    
    Returns:
        bool: True if sufficient, False otherwise.
    """
    return current_count >= minimum_required


def exit_on_insufficiency(
    current_count: int,
    minimum_required: int,
    missing_features: Optional[list] = None,
    logger_instance: Optional[logging.Logger] = None
) -> None:
    """
    Log a data insufficiency error and exit the program with code 1.
    
    This function is designed to be called when data requirements are not met.
    It logs the exact count of retrieved vs. required records and exits.
    
    Args:
        current_count: The number of records currently available.
        minimum_required: The minimum number of records required.
        missing_features: Optional list of features causing insufficiency.
        logger_instance: Optional logger instance. If None, uses the module logger.
    
    Exits:
        sys.exit(1): Always exits with code 1 if called.
    """
    if logger_instance is None:
        logger_instance = logger
    
    error = DataInsufficiencyError(
        retrieved_count=current_count,
        required_count=minimum_required,
        missing_features=missing_features
    )
    
    logger_instance.error(str(error))
    sys.exit(1)
