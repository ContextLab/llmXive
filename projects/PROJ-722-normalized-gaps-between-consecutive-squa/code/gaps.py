"""
Gap calculation and normalization utilities for squarefree number analysis.

This module provides functions to:
1. Calculate raw gaps between consecutive squarefree numbers
2. Normalize gaps by the empirical mean
3. Persist gap data to Parquet format
"""
import numpy as np
from typing import List
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from code.logging_config import get_logger

logger = get_logger(__name__)


def calculate_gaps(squarefree_list: List[int]) -> List[int]:
    """
    Calculate raw gaps between consecutive squarefree numbers.
    
    Given a sorted list of squarefree numbers [s_1, s_2, ..., s_n],
    computes the gaps: Δ_i = s_{i+1} - s_i for i = 1 to n-1.
    
    Args:
        squarefree_list: Sorted list of squarefree integers.
        
    Returns:
        List of gap values (differences between consecutive elements).
        
    Raises:
        ValueError: If the input list has fewer than 2 elements.
    """
    if len(squarefree_list) < 2:
        raise ValueError(
            f"Cannot calculate gaps: input list must have at least 2 elements, "
            f"got {len(squarefree_list)}"
        )
    
    # Convert to numpy array for efficient vectorized operation
    arr = np.array(squarefree_list, dtype=np.int64)
    gaps = np.diff(arr)
    
    # Ensure all gaps are positive (sanity check)
    if np.any(gaps <= 0):
        logger.warning(f"Found non-positive gaps in input: {gaps[gaps <= 0]}")
    
    return gaps.tolist()


def normalize_gaps(gaps: List[int]) -> np.ndarray:
    """
    Normalize gaps by dividing by the empirical mean.
    
    Computes g_i = Δ_i / Δ̄ where Δ̄ is the mean of all gaps.
    The resulting normalized gaps should have a mean of exactly 1.0.
    
    Args:
        gaps: List of raw gap values (integers).
        
    Returns:
        NumPy array of normalized gaps (floats).
        
    Raises:
        ValueError: If the input list is empty.
        ZeroDivisionError: If the mean of gaps is zero (should not happen with valid data).
    """
    if not gaps:
        raise ValueError("Cannot normalize gaps: input list is empty")
    
    gaps_array = np.array(gaps, dtype=np.float64)
    mean_gap = np.mean(gaps_array)
    
    if mean_gap == 0:
        raise ZeroDivisionError(
            "Cannot normalize gaps: mean of gaps is zero. "
            "This indicates invalid input data."
        )
    
    normalized = gaps_array / mean_gap
    
    # Verify the mean is 1.0 (within floating point precision)
    # This is a sanity check, not an assertion that would break execution
    actual_mean = np.mean(normalized)
    if abs(actual_mean - 1.0) > 1e-10:
        logger.warning(
            f"Normalized gaps mean is {actual_mean}, expected 1.0. "
            f"Difference: {abs(actual_mean - 1.0)}"
        )
    
    return normalized


def save_normalized_gaps(
    normalized_gaps: np.ndarray,
    N: int,
    output_dir: str = "data/raw"
) -> str:
    """
    Save normalized gaps to a Parquet file.
    
    Args:
        normalized_gaps: NumPy array of normalized gap values.
        N: The cutoff value used for generating squarefree numbers.
        output_dir: Directory to save the output file.
        
    Returns:
        Path to the saved Parquet file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"gaps_N={N}.parquet"
    file_path = output_path / filename
    
    # Create PyArrow table
    table = pa.table({
        'normalized_gap': normalized_gaps,
        'N': np.full(len(normalized_gaps), N, dtype=np.int64)
    })
    
    # Write to Parquet
    pq.write_table(table, file_path)
    
    logger.info(f"Saved {len(normalized_gaps)} normalized gaps to {file_path}")
    
    return str(file_path)


def validate_normalized_gaps_mean(normalized_gaps: np.ndarray, tolerance: float = 1e-9) -> bool:
    """
    Validate that the mean of normalized gaps is 1.0 within tolerance.
    
    This implements the theoretical requirement that normalized gaps
    should have a mean of exactly 1.0 (SC-001).
    
    Args:
        normalized_gaps: NumPy array of normalized gap values.
        tolerance: Maximum allowed deviation from 1.0.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        AssertionError: If the mean is not within tolerance of 1.0.
    """
    mean_value = np.mean(normalized_gaps)
    
    if abs(mean_value - 1.0) > tolerance:
        raise AssertionError(
            f"Validation failed: mean of normalized gaps is {mean_value}, "
            f"expected 1.0 (tolerance: {tolerance}). "
            f"This violates the theoretical requirement (SC-001)."
        )
    
    logger.info(f"Validation passed: mean of normalized gaps is {mean_value} (within {tolerance})")
    return True


def save_normalized_gaps_with_validation(
    gaps: List[int],
    N: int,
    output_dir: str = "data/raw",
    tolerance: float = 1e-9
) -> str:
    """
    Calculate, normalize, validate, and save gaps in one workflow.
    
    This function orchestrates the full pipeline for a given N:
    1. Calculates raw gaps from a list of squarefree numbers (passed as gaps input for simplicity here, 
       assuming the caller has the squarefree list or gaps already, but per task T015/T016 flow, 
       this is often called after gaps are derived).
    
    Note: This function expects `gaps` to be the raw integer gaps (as produced by calculate_gaps).
    It normalizes them, validates the mean is 1.0 (SC-001), and saves to Parquet.
    
    Args:
        gaps: List of raw integer gaps.
        N: The cutoff value used for generating squarefree numbers.
        output_dir: Directory to save the output file.
        tolerance: Tolerance for the mean validation (SC-001).
        
    Returns:
        Path to the saved Parquet file.
        
    Raises:
        AssertionError: If the normalized mean is not within tolerance of 1.0.
    """
    # Normalize the gaps
    normalized = normalize_gaps(gaps)
    
    # Validate against SC-001: Theoretical mean must be 1.0
    validate_normalized_gaps_mean(normalized, tolerance=tolerance)
    
    # Save to Parquet
    return save_normalized_gaps(normalized, N, output_dir)
