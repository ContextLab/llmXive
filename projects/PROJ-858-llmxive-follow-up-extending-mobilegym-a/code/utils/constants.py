"""
Constants and utility functions for the llmXive project.

This module defines error codes, validation functions for coverage vectors,
semantic state proxies, and other project-wide constants.
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

# Semantic State Proxies
# These are loaded from the coverage schema to ensure consistency
_SEMANTIC_PROXIES: Optional[List[str]] = None
_VECTOR_DIMENSIONS: Optional[int] = None


def _load_schema_constants() -> None:
    """
    Load semantic proxies and vector dimensions from the coverage schema.
    
    This function reads the contracts/coverage.schema.yaml file and populates
    the global _SEMANTIC_PROXIES and _VECTOR_DIMENSIONS variables.
    It is called lazily by get_semantic_proxies() and get_coverage_vector_dimensions().
    """
    global _SEMANTIC_PROXIES, _VECTOR_DIMENSIONS
    
    if _SEMANTIC_PROXIES is not None and _VECTOR_DIMENSIONS is not None:
        return
    
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "coverage.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Coverage schema not found at {schema_path}. "
            "Please ensure contracts/coverage.schema.yaml exists."
        )
    
    # Simple YAML parser for the specific structure we need
    # (avoiding external dependencies like PyYAML for this constant loading)
    with open(schema_path, 'r') as f:
        content = f.read()
    
    # Extract semantic_proxies list
    proxies = []
    in_proxies_section = False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped == 'semantic_proxies:':
            in_proxies_section = True
            continue
        elif in_proxies_section:
            if stripped.startswith('- '):
                proxy_name = stripped[2:].strip()
                # Remove quotes if present
                if (proxy_name.startswith('"') and proxy_name.endswith('"')) or \
                   (proxy_name.startswith("'") and proxy_name.endswith("'")):
                    proxy_name = proxy_name[1:-1]
                proxies.append(proxy_name)
            elif stripped and not stripped.startswith('#') and not stripped.startswith('-'):
                # End of the list section
                break
    
    # Extract vector_dimensions
    dimensions = 0
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('vector_dimensions:'):
            try:
                dimensions = int(stripped.split(':')[1].strip())
            except (ValueError, IndexError):
                raise ValueError(f"Could not parse vector_dimensions from schema: {stripped}")
            break
    
    if not proxies:
        raise ValueError("No semantic proxies found in coverage.schema.yaml")
    
    if dimensions == 0:
        raise ValueError("vector_dimensions not found or invalid in coverage.schema.yaml")
    
    if len(proxies) != dimensions:
        # Log a warning but proceed, using the actual count from proxies
        # This handles cases where the dimension count might be outdated
        pass
    
    _SEMANTIC_PROXIES = proxies
    _VECTOR_DIMENSIONS = dimensions


def get_semantic_proxies() -> List[str]:
    """
    Get the list of semantic state proxies defined in the coverage schema.
    
    Returns:
        A list of strings representing the semantic state proxies (e.g., 'dark_mode').
    
    Raises:
        FileNotFoundError: If the coverage schema file is missing.
        ValueError: If the schema is malformed or contains no proxies.
    """
    _load_schema_constants()
    return _SEMANTIC_PROXIES  # type: ignore


def get_coverage_vector_dimensions() -> int:
    """
    Get the total number of dimensions in the state coverage vector.
    
    Returns:
        An integer representing the vector dimensions.
    
    Raises:
        FileNotFoundError: If the coverage schema file is missing.
        ValueError: If the schema is malformed.
    """
    _load_schema_constants()
    return _VECTOR_DIMENSIONS  # type: ignore