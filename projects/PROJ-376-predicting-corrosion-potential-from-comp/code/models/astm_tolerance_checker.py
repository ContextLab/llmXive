"""
ASTM Tolerance Checker Module

This module provides functionality to check model performance against the
ASTM G59 tolerance standard. It ensures that RMSE comparisons are always
performed against a defined tolerance value (SC-002).
"""

import logging
from typing import Tuple, Dict, Any, Optional

from utils.astm_g59_parser import (
    get_tolerance_value,
    get_tolerance_source_info,
    validate_tolerance_for_comparison
)
from utils.logging import get_logger

logger: logging.Logger = get_logger(__name__)


def check_rmse_against_tolerance(
    rmse_value: float,
    rmse_unit: str,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare model RMSE against the ASTM G59 tolerance standard.

    This function ensures that a comparison is always performed against a
    defined tolerance value, preventing 'N/A' paths in the results.

    Args:
        rmse_value: The RMSE value from the model evaluation.
        rmse_unit: The unit of the RMSE value (e.g., 'mV', 'V').
        config_path: Optional path to the tolerance configuration file.

    Returns:
        Dictionary containing:
            - rmse_value: float (input RMSE value)
            - rmse_unit: str (input RMSE unit)
            - tolerance_value: float (tolerance from config)
            - tolerance_unit: str (tolerance unit)
            - comparison_result: str ('within_tolerance', 'exceeds_tolerance', 'unknown')
            - difference: float (difference between RMSE and tolerance)
            - source_info: dict (source information for the tolerance)
            - conclusion: str (human-readable conclusion)

    Raises:
        ValueError: If RMSE value is invalid.
        CorrosionPipelineError: If tolerance configuration cannot be loaded.
    """
    if rmse_value < 0:
        raise ValueError(f"RMSE value must be non-negative, got {rmse_value}")

    # Load tolerance configuration
    tolerance_value, tolerance_unit = get_tolerance_value(config_path)
    source_info = get_tolerance_source_info(config_path)

    # Validate tolerance
    validate_tolerance_for_comparison(tolerance_value, tolerance_unit)

    # Normalize units for comparison
    rmse_normalized = rmse_value
    tolerance_normalized = tolerance_value

    if rmse_unit.lower() == 'v' and tolerance_unit.lower() == 'mV':
        rmse_normalized = rmse_value * 1000
    elif rmse_unit.lower() == 'mV' and tolerance_unit.lower() == 'v':
        tolerance_normalized = tolerance_value * 1000

    # Perform comparison
    difference = rmse_normalized - tolerance_normalized

    if difference <= 0:
        comparison_result = 'within_tolerance'
        conclusion = (
            f"Model RMSE ({rmse_normalized:.2f} mV) is within the ASTM G59 "
            f"tolerance ({tolerance_normalized:.2f} mV). "
            f"Difference: {abs(difference):.2f} mV."
        )
    else:
        comparison_result = 'exceeds_tolerance'
        conclusion = (
            f"Model RMSE ({rmse_normalized:.2f} mV) exceeds the ASTM G59 "
            f"tolerance ({tolerance_normalized:.2f} mV). "
            f"Exceeds by: {difference:.2f} mV."
        )

    result = {
        'rmse_value': rmse_value,
        'rmse_unit': rmse_unit,
        'tolerance_value': tolerance_value,
        'tolerance_unit': tolerance_unit,
        'comparison_result': comparison_result,
        'difference': difference,
        'source_info': source_info,
        'conclusion': conclusion
    }

    logger.info(f"ASTM G59 tolerance comparison: {comparison_result}")
    logger.info(f"Conclusion: {conclusion}")

    return result


def format_comparison_report(results: Dict[str, Any]) -> str:
    """
    Format the tolerance comparison results into a human-readable report.

    Args:
        results: Dictionary from check_rmse_against_tolerance().

    Returns:
        Formatted string report.
    """
    report_lines = [
        "=" * 60,
        "ASTM G59 Tolerance Comparison Report",
        "=" * 60,
        "",
        f"Model RMSE: {results['rmse_value']:.2f} {results['rmse_unit']}",
        f"Tolerance:  {results['tolerance_value']:.2f} {results['tolerance_unit']}",
        f"Difference: {results['difference']:.2f} mV",
        "",
        f"Comparison Result: {results['comparison_result'].upper()}",
        "",
        "Source Information:",
        f"  - Source: {results['source_info']['source']}",
        f"  - Standard Reference: {results['source_info']['standard_reference']}",
        f"  - Verified: {results['source_info']['verified']}",
        "",
        "Notes:",
        f"  {results['source_info']['notes']}",
        "",
        "Conclusion:",
        f"  {results['conclusion']}",
        "",
        "=" * 60
    ]

    return "\n".join(report_lines)