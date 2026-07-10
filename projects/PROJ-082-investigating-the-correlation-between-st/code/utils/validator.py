"""
Validation utilities for the meta-analysis pipeline.
Specifically handles validation of effect sizes and input data integrity.
"""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)


def validate_effect_size(
    r_value: Optional[float],
    n_value: Optional[int],
    study_id: str,
    row_index: int
) -> Tuple[bool, Optional[str]]:
    """
    Validates the presence and validity of effect size data (r, n).

    Args:
        r_value: The correlation coefficient (r).
        n_value: The sample size (n).
        study_id: Identifier for the study (for logging).
        row_index: The row index in the source file (for logging).

    Returns:
        A tuple (is_valid, error_message).
        If valid, error_message is None.
        If invalid, is_valid is False and error_message explains the reason.
    """
    if r_value is None or n_value is None:
        return False, f"Missing effect size data (r={r_value}, n={n_value})"

    if not isinstance(n_value, int) or n_value <= 0:
        return False, f"Invalid sample size: {n_value} (must be positive integer)"

    if not isinstance(r_value, (int, float)):
        return False, f"Invalid correlation value: {r_value} (must be numeric)"

    # Check for NaN or Inf
    if math.isnan(r_value) or math.isinf(r_value):
        return False, f"Invalid correlation value: {r_value} (NaN or Inf)"

    # Check range [-1, 1]
    if not (-1.0 <= r_value <= 1.0):
        return False, f"Correlation value out of range: {r_value} (must be between -1 and 1)"

    return True, None


def validate_study_row(
    row: Dict[str, Any],
    study_id_col: str = "study_id",
    r_col: str = "r",
    n_col: str = "n"
) -> Tuple[bool, Optional[str]]:
    """
    Validates a single study row extracted from CSV/JSON.

    Args:
        row: Dictionary representing the study row.
        study_id_col: Key for the study ID.
        r_col: Key for the correlation coefficient.
        n_col: Key for the sample size.

    Returns:
        A tuple (is_valid, error_message).
    """
    study_id = row.get(study_id_col, "Unknown")
    row_idx = row.get("row_index", -1)

    r_val = row.get(r_col)
    n_val = row.get(n_col)

    # Convert string numbers to float/int if necessary
    if isinstance(r_val, str):
        try:
            r_val = float(r_val)
        except ValueError:
            return False, f"Cannot convert r value '{r_val}' to float"

    if isinstance(n_val, str):
        try:
            n_val = int(float(n_val)) # Handle "10.0" -> 10
        except ValueError:
            return False, f"Cannot convert n value '{n_val}' to integer"

    return validate_effect_size(r_val, n_val, study_id, row_idx)


def filter_valid_studies(
    studies: List[Dict[str, Any]],
    r_col: str = "r",
    n_col: str = "n",
    study_id_col: str = "study_id"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filters a list of studies, keeping only those with valid effect sizes.
    Logs excluded studies.

    Args:
        studies: List of study dictionaries.
        r_col: Key for correlation.
        n_col: Key for sample size.
        study_id_col: Key for study ID.

    Returns:
        A tuple (valid_studies, excluded_studies).
    """
    valid = []
    excluded = []

    for study in studies:
        is_valid, error_msg = validate_study_row(
            study, study_id_col, r_col, n_col
        )

        if is_valid:
            valid.append(study)
        else:
            study_id = study.get(study_id_col, "Unknown")
            row_idx = study.get("row_index", -1)
            logger.warning(
                f"Excluding study {study_id} (Row {row_idx}): {error_msg}"
            )
            excluded.append({
                "study": study,
                "reason": error_msg
            })

    if excluded:
        logger.info(f"Filtered out {len(excluded)} studies due to invalid effect sizes.")

    return valid, excluded
