import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from utils.logging import get_logger, LlmXiveError
from data.schema import DiscreteStateVector, QuantizationLevel

logger = get_logger(__name__)

class DegeneracyError(LlmXiveError):
    """Raised when data degeneracy (e.g., collapse) is detected."""
    pass

def validate_discrete_state_vector(
    state_vector: DiscreteStateVector,
    quantization_level: QuantizationLevel,
    min_unique_values: int = 2
) -> Tuple[bool, str]:
    """
    Validates a single discrete state vector for degeneracy.
    
    Checks:
    1. Range validity: All values must be within [0, 2^bits - 1].
    2. Degeneracy (Collapse): Checks if the number of unique values is too low
       (indicating a "1-bit collapse" or similar information loss).
    
    Args:
        state_vector: The list of integer values to validate.
        quantization_level: The target quantization level (4, 8, or 16 bits).
        min_unique_values: Minimum number of unique values required to avoid collapse flag.
    
    Returns:
        Tuple of (is_valid, message).
    
    Raises:
        DegeneracyError: If the vector is valid but degenerate (collapsed).
    """
    if not state_vector:
        return False, "Empty state vector"

    try:
        arr = np.array(state_vector)
    except (ValueError, TypeError) as e:
        raise DegeneracyError(f"Invalid state vector format: {e}")

    bits = quantization_level.value
    max_val = (1 << bits) - 1
    min_val = 0

    # Check Range
    if np.any(arr < min_val) or np.any(arr > max_val):
        return False, f"Values out of range [{min_val}, {max_val}] for {bits}-bit quantization"

    # Check Degeneracy (Collapse)
    unique_count = len(np.unique(arr))
    
    if unique_count < min_unique_values:
        raise DegeneracyError(
            f"Degenerate data detected: Only {unique_count} unique values found "
            f"in {len(arr)}-dimensional vector. "
            f"Likely collapse for {bits}-bit quantization (min required: {min_unique_values})."
        )
    
    # Optional: Warn if unique count is significantly lower than expected capacity
    # but still above the hard failure threshold
    capacity = max_val + 1
    if unique_count < (capacity * 0.01) and capacity > 16:
        logger.warning(
            f"Low information density detected: {unique_count} unique values "
            f"out of {capacity} possible for {bits}-bit quantization."
        )

    return True, "Valid"

def validate_dataset_for_degeneracy(
    data: List[DiscreteStateVector],
    quantization_level: QuantizationLevel,
    collapse_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Scans a dataset of state vectors for degeneracy patterns.
    
    Args:
        data: List of state vectors (list of lists of ints).
        quantization_level: Target quantization level.
        collapse_threshold: Fraction of vectors that can be degenerate before 
                            flagging the whole dataset as "Invalid Data".
    
    Returns:
        Dictionary with validation results:
        {
            "is_valid": bool,
            "degenerate_count": int,
            "total_count": int,
            "degeneracy_rate": float,
            "details": List[str] (sample error messages)
        }
    """
    total_count = len(data)
    if total_count == 0:
        return {
            "is_valid": True,
            "degenerate_count": 0,
            "total_count": 0,
            "degeneracy_rate": 0.0,
            "details": []
        }

    degenerate_count = 0
    error_details = []

    for i, vector in enumerate(data):
        try:
            validate_discrete_state_vector(vector, quantization_level)
        except DegeneracyError as e:
            degenerate_count += 1
            if len(error_details) < 5:  # Keep log size manageable
                error_details.append(f"Vector {i}: {str(e)}")

    degeneracy_rate = degenerate_count / total_count
    is_valid = degeneracy_rate <= collapse_threshold

    result = {
        "is_valid": is_valid,
        "degenerate_count": degenerate_count,
        "total_count": total_count,
        "degeneracy_rate": degeneracy_rate,
        "details": error_details
    }

    if not is_valid:
        logger.error(
            f"Dataset validation FAILED: {degenerate_count}/{total_count} vectors "
            f"({degeneracy_rate:.2%}) show degeneracy/collapse."
        )
    else:
        logger.info(
            f"Dataset validation PASSED: {degenerate_count}/{total_count} vectors "
            f"({degeneracy_rate:.2%}) show degeneracy (below threshold)."
        )

    return result

def check_single_vector_degeneracy(
    vector: DiscreteStateVector,
    bits: int
) -> Dict[str, Any]:
    """
    Quick check for a single vector's degeneracy status.
    Returns a dict with 'collapsed' boolean and 'unique_count'.
    """
    arr = np.array(vector)
    unique_count = len(np.unique(arr))
    max_val = (1 << bits) - 1
    
    # A "1-bit collapse" typically means the signal is binary (0 or 1) or constant
    # We define collapse as having fewer than 2 unique values or extremely low entropy relative to bits
    is_collapsed = unique_count < 2
    
    return {
        "unique_count": int(unique_count),
        "collapsed": bool(is_collapsed),
        "bits": bits,
        "max_possible": int(max_val)
    }
