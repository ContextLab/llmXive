import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from utils.logging import get_logger
from config import get_reductions

logger = get_logger(__name__)


def validate_reduction_levels(
    available_levels: List[int],
    required_levels: Optional[List[int]] = None
) -> Tuple[List[int], List[int]]:
    """
    Validates available reduction levels against required levels.

    Args:
        available_levels: List of reduction levels found in the data source.
        required_levels: List of reduction levels expected (from config/research.md).
                       If None, uses default from config.

    Returns:
        Tuple of (valid_levels, missing_levels)
    """
    if required_levels is None:
        required_levels = get_reductions()

    valid_levels = [lvl for lvl in required_levels if lvl in available_levels]
    missing_levels = [lvl for lvl in required_levels if lvl not in available_levels]

    if missing_levels:
        logger.warning(
            f"Missing reduction levels: {missing_levels}. "
            f"Proceeding with available levels: {valid_levels}"
        )

    return valid_levels, missing_levels


def check_file_integrity(file_path: Path) -> bool:
    """
    Checks if a file exists and is not empty/corrupted.

    Args:
        file_path: Path to the file to check.

    Returns:
        True if file is valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        # Attempt to read the file to check for corruption
        if file_path.suffix == '.csv':
            pd.read_csv(file_path, nrows=1)
        elif file_path.suffix == '.parquet':
            pd.read_parquet(file_path)
        elif file_path.suffix == '.npy':
            import numpy as np
            np.load(file_path)
        else:
            # Generic read for other formats
            with open(file_path, 'rb') as f:
                f.read(1024)  # Read first 1KB

        return True
    except Exception as e:
        logger.error(f"File corrupted or unreadable: {file_path}. Error: {e}")
        return False


def handle_corrupted_file(file_path: Path) -> bool:
    """
    Handles a corrupted file by logging the error and returning False.

    Args:
        file_path: Path to the corrupted file.

    Returns:
        False indicating the file should be skipped.
    """
    logger.error(f"Skipping corrupted file: {file_path}")
    return False


def handle_missing_reduction(
    material: str,
    reduction: int,
    available_data: Dict[str, Dict[int, Any]]
) -> bool:
    """
    Handles missing metal/reduction combination.

    Args:
        material: Material name (e.g., 'Al', 'Cu', 'Ni').
        reduction: Reduction level that is missing.
        available_data: Dictionary of available data to check against.

    Returns:
        False indicating this entry should be skipped.
    """
    logger.warning(
        f"Missing data for {material} at {reduction}% reduction. "
        "Skipping this entry and proceeding with available data."
    )
    return False


def calculate_reliability_metrics(
    df: pd.DataFrame,
    confidence_col: str = 'confidence',
    threshold: float = 0.1
) -> Dict[str, float]:
    """
    Calculates reliability metrics for a dataset.

    Args:
        df: DataFrame containing orientation data.
        confidence_col: Name of the confidence column.
        threshold: Minimum confidence threshold.

    Returns:
        Dictionary with 'total_points', 'filtered_points', 'reliability_score'.
    """
    total_points = len(df)
    filtered_points = len(df[df[confidence_col] >= threshold])
    filtered_ratio = filtered_points / total_points if total_points > 0 else 0.0

    return {
        'total_points': total_points,
        'filtered_points': filtered_points,
        'filtered_ratio': filtered_ratio,
        'reliability_score': filtered_ratio
    }


def apply_exclusion_logic(
    metrics: Dict[str, float],
    exclusion_threshold: float = 0.5
) -> Tuple[bool, str]:
    """
    Applies exclusion logic based on reliability metrics.

    Args:
        metrics: Reliability metrics from calculate_reliability_metrics.
        exclusion_threshold: Threshold for filtering ratio above which
                           samples are excluded (default 0.5 = 50%).

    Returns:
        Tuple of (should_exclude, reason)
    """
    filtered_ratio = metrics.get('filtered_ratio', 0.0)

    if filtered_ratio > exclusion_threshold:
        reason = (
            f"Low reliability: {filtered_ratio:.2%} of points filtered out. "
            f"Exceeds threshold of {exclusion_threshold:.0%}."
        )
        logger.warning(reason)
        return True, reason

    return False, "Reliability acceptable"


def process_with_error_handling(
    data_source: Any,
    process_func: Any,
    *args,
    **kwargs
) -> Tuple[Optional[Any], List[str]]:
    """
    Generic wrapper to process data with comprehensive error handling.

    Args:
        data_source: The data source to process.
        process_func: The function to apply to the data.
        *args: Additional arguments for process_func.
        **kwargs: Additional keyword arguments for process_func.

    Returns:
        Tuple of (result, list_of_warnings)
    """
    warnings = []

    try:
        if data_source is None:
            raise ValueError("Data source is None")

        result = process_func(data_source, *args, **kwargs)
        return result, warnings

    except FileNotFoundError as e:
        warnings.append(f"File not found: {e}")
        logger.error(f"Skipping data source due to missing file: {e}")
        return None, warnings

    except pd.errors.EmptyDataError:
        warnings.append("File is empty or corrupted")
        logger.error("Skipping empty/corrupted file")
        return None, warnings

    except Exception as e:
        warnings.append(f"Unexpected error: {e}")
        logger.error(f"Error processing data: {e}", exc_info=True)
        return None, warnings


def main():
    """
    Main entry point for error handling demonstrations.
    This function demonstrates the error handling capabilities.
    """
    logger.info("Starting error handling module demonstration")

    # Example: Validate reduction levels
    available = [0, 10, 20, 30, 50, 60]
    required = [0, 10, 20, 30, 40, 50, 60, 70, 80]

    valid, missing = validate_reduction_levels(available, required)
    logger.info(f"Valid levels: {valid}")
    logger.info(f"Missing levels: {missing}")

    # Example: Reliability metrics
    sample_df = pd.DataFrame({
        'confidence': [0.05, 0.15, 0.2, 0.08, 0.3, 0.12]
    })

    metrics = calculate_reliability_metrics(sample_df)
    logger.info(f"Reliability metrics: {metrics}")

    should_exclude, reason = apply_exclusion_logic(metrics)
    if should_exclude:
        logger.warning(f"Sample excluded: {reason}")
    else:
        logger.info(f"Sample included: {reason}")

    logger.info("Error handling module demonstration complete")


if __name__ == '__main__':
    main()
