"""
Constants and utility functions for the llmXive project.

This module defines error codes, validation functions for coverage vectors,
and other project-wide constants.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ErrorCodes:
    """Standard error codes used across the project."""
    CONFIGURATION_ERROR = "CONFIG_001"
    DATA_ERROR = "DATA_001"
    SCHEDULER_ERROR = "SCHED_001"
    COVERAGE_ERROR = "COV_001"
    PARALLEL_PROCESSING_ERROR = "PAR_001"
    TIMEOUT_ERROR = "TIME_001"
    VALIDATION_ERROR = "VAL_001"


def is_valid_coverage_vector(vector: List[int]) -> bool:
    """
    Validate that a list represents a valid binary coverage vector.
    
    Args:
        vector: A list of integers (should be 0s and 1s)
    
    Returns:
        True if the vector is valid, False otherwise
    """
    if not isinstance(vector, list):
        return False
    
    if len(vector) == 0:
        return False
    
    for item in vector:
        if item not in (0, 1):
            return False
    
    return True


def calculate_coverage_ratio(vector: List[int]) -> float:
    """
    Calculate the ratio of covered states (1s) to total states.
    
    Args:
        vector: A binary coverage vector
    
    Returns:
        A float between 0.0 and 1.0 representing the coverage ratio
    """
    if not is_valid_coverage_vector(vector):
        raise ValueError(f"Invalid coverage vector: {vector}")
    
    if len(vector) == 0:
        return 0.0
    
    covered_count = sum(vector)
    total_count = len(vector)
    
    return covered_count / total_count


# Project-wide constants
DEFAULT_TIME_LIMIT_HOURS = 6
SUCCESS_THRESHOLD = 0.7
MIN_COVERAGE_THRESHOLD = 0.05
MAX_COVERAGE_THRESHOLD = 0.95
SWEET_SPOT_MIN = 0.3
SWEET_SPOT_MAX = 0.7
MAX_WORKERS_DEFAULT = 8
MAX_WORKERS_HIGH_CONTENTION = 32
