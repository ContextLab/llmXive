"""
Failure Detection Logic for Hierarchical Bayesian Tests.

This module explicitly defines how Hierarchical Bayesian test failure is detected
based on Effective Sample Size (ESS) thresholds as per Amended FR-007.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logging import get_logger
from src.utils.config import get_project_root

logger = get_logger(__name__)

# Threshold constants defined in Amended FR-007
ESS_THRESHOLD = 100
MIN_SAMPLE_SIZE = 5


def check_hierarchical_convergence(ess_value: float) -> bool:
    """
    Check if the Hierarchical Bayesian test has failed to converge based on ESS.

    Args:
        ess_value (float): The Effective Sample Size extracted from the Bilby/Dynesty
                           output JSON (key: 'effective_sample_size').

    Returns:
        bool: True if the test has FAILED to converge (ESS < 100), False otherwise.
              (Note: Returns True on failure to align with "check for failure" semantics).
    """
    if ess_value is None:
        logger.warning("ESS value is None. Assuming convergence failure.")
        return True

    is_failed = ess_value < ESS_THRESHOLD
    if is_failed:
        logger.warning(
            f"Hierarchical convergence check FAILED: ESS={ess_value:.2f} "
            f" < threshold {ESS_THRESHOLD}."
        )
    else:
        logger.info(
            f"Hierarchical convergence check PASSED: ESS={ess_value:.2f} "
            f" >= threshold {ESS_THRESHOLD}."
        )
    return is_failed


def check_sample_size(n_events: int) -> bool:
    """
    Check if the sample size is too small for robust hierarchical inference.

    Args:
        n_events (int): The number of events in the analysis set.

    Returns:
        bool: True if the sample size is too small (N < 5), False otherwise.
    """
    is_failed = n_events < MIN_SAMPLE_SIZE
    if is_failed:
        logger.warning(
            f"Sample size check FAILED: N={n_events} < threshold {MIN_SAMPLE_SIZE}."
        )
    else:
        logger.info(
            f"Sample size check PASSED: N={n_events} >= threshold {MIN_SAMPLE_SIZE}."
        )
    return is_failed


def load_ess_from_bilby_output(output_path: str) -> Optional[float]:
    """
    Load the Effective Sample Size (ESS) from a Bilby/Dynesty output JSON file.

    Args:
        output_path (str): Path to the Bilby/Dynesty output JSON file.

    Returns:
        Optional[float]: The ESS value if found, None otherwise.
    """
    try:
        path = Path(output_path)
        if not path.exists():
            logger.error(f"Output file not found: {output_path}")
            return None

        with open(path, 'r') as f:
            data = json.load(f)

        # Bilby/Dynesty typically stores summary stats in 'samples' or top level
        # Depending on the version/format, it might be 'effective_sample_size' or nested
        ess = data.get('effective_sample_size')
        if ess is None and 'samples' in data:
            # Fallback: try to calculate from samples if not explicitly stored
            samples = data['samples']
            if isinstance(samples, list) and len(samples) > 0:
                logger.info("Calculating ESS from samples (fallback).")
                # Simple approximation or just return length if specific ESS calc not available
                # For strict compliance, we rely on the explicit key.
                return None

        return float(ess) if ess is not None else None

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse ESS from {output_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {output_path}: {e}")
        return None
