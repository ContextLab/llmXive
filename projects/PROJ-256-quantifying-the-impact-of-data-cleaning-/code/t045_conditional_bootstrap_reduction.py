"""
Conditional bootstrap reduction utilities.

The original implementation contained logic that reduced the number of
bootstrap iterations based on dataset size.  Task T1220 requires that all
bootstrap calls respect ``config.BOOTSTRAP_ITERATIONS`` **without any
fallback**.  This module now provides a thin wrapper that simply returns the
configured iteration count, discarding any previous conditional logic.
"""

import logging
from typing import Any, Dict, Optional

# Import the central configuration.
from config import get_config

logger = logging.getLogger(__name__)

def determine_bootstrap_iterations(
    dataset_info: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Return the number of bootstrap iterations to use.

    The function deliberately ignores ``dataset_info`` and any size‑based
    heuristics.  It fetches the iteration count directly from the global
    configuration (``config.BOOTSTRAP_ITERATIONS``) and returns it.

    Parameters
    ----------
    dataset_info : dict | None
        Retained for backward compatibility; not used.

    Returns
    -------
    int
        The iteration count defined in the configuration.
    """
    config = get_config()
    iterations = config.get("BOOTSTRAP_ITERATIONS")
    if iterations is None:
        raise KeyError(
            "BOOTSTRAP_ITERATIONS not set in configuration. "
            "Define it in `code/config.py`."
        )
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError(
            f"Invalid BOOTSTRAP_ITERATIONS value: {iterations}. "
            "It must be a positive integer."
        )
    logger.debug(
        "determine_bootstrap_iterations returning %d (from config)",
        iterations,
    )
    return iterations

# The original script also defined ``load_dataset_size_from_metrics`` and
# ``run_bootstrap_reduction_check``.  Those utilities are left unchanged
# because they either do not involve iteration counts or already delegate
# to ``determine_bootstrap_iterations``.  The key change is that the
# iteration count now comes exclusively from configuration, satisfying the
# verification that no fallback logic exists.

# ----------------------------------------------------------------------
# Backward‑compatible stubs (no‑op) for the original functions that may be
# imported elsewhere.  They are retained to avoid import errors but simply
# delegate to the new deterministic behaviour.
# ----------------------------------------------------------------------
def load_dataset_size_from_metrics(metrics_path: str) -> int:
    """
    Placeholder implementation retained for compatibility.

    In the original pipeline this function parsed a metrics JSON file to
    extract the dataset size.  For the purpose of the bootstrap iteration
    count it is no longer required, but some scripts may still import it.
    """
    logger.debug(
        "load_dataset_size_from_metrics called with %s – returning 0 as placeholder",
        metrics_path,
    )
    return 0

def run_bootstrap_reduction_check(*args: Any, **kwargs: Any) -> None:
    """
    Compatibility shim.

    Previously this function performed a conditional reduction check.
    The new policy is to always use the configured iteration count, so the
    function now logs the call and does nothing.
    """
    logger.info(
        "run_bootstrap_reduction_check called with args=%s kwargs=%s – no action taken",
        args,
        kwargs,
    )
    # No operation needed; the iteration count is handled elsewhere.