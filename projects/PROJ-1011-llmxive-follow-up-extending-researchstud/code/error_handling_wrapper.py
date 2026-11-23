"""
Error‑handling wrapper for the llmXive pipeline.

This script demonstrates the required behaviour for task **T008**:
- It attempts a data‑fetch operation.
- On a simulated failure it raises ``DataFetchError`` (from
  ``utils.error_handling``), logs a model‑fallback switch via the
  helper functions in ``utils.logging_config``, and exits with a
  non‑zero status code.
- When run without the ``--simulate-failure`` flag it exits cleanly
  with status 0, indicating a successful fetch.

The test suite (`test_error_wrapper`) invokes this script with the
``--simulate-failure`` flag and asserts that the process terminates
with a non‑zero exit code while the appropriate log entries are
written.
"""

import sys
from utils.logging_config import get_logger, log_model_switch, log_fallback_failure
from utils.error_handling import DataFetchError

def _perform_fetch(simulate_failure: bool) -> None:
    """
    Simulated fetch routine.

    Parameters
    ----------
    simulate_failure : bool
        When ``True`` the function raises ``DataFetchError`` to mimic a
        network or pay‑wall failure. When ``False`` it completes
        silently, representing a successful fetch.
    """
    if simulate_failure:
        # In a real implementation this would be an HTTP request that
        # raised an exception or returned a non‑2xx status.
        raise DataFetchError("Simulated data‑fetch failure for testing.")
    # No‑op for successful fetch – placeholder for real logic.

def main() -> None:
    """
    Entry point for the wrapper.

    The script parses ``--simulate-failure`` from ``sys.argv``.  If the
    flag is present the fetch is forced to fail, the fallback is
    logged, and the process exits with status 1.  Otherwise it exits
    with status 0.
    """
    logger = get_logger(__name__)

    simulate = "--simulate-failure" in sys.argv

    try:
        _perform_fetch(simulate)
        logger.info("Data fetch succeeded.")
        sys.exit(0)
    except DataFetchError as exc:
        # Log the model‑fallback switch – the exact model names are
        # placeholders because the wrapper is generic.
        primary_model = "primary_model"
        fallback_model = "fallback_model"
        log_model_switch(primary_model, fallback_model)
        # Also log the failure explicitly.
        logger.error(f"Data fetch error: {exc}")
        # Optionally log a more detailed fallback failure.
        log_fallback_failure(primary_model, fallback_model, exc)
        # Exit with a non‑zero code to satisfy the “fails loudly” requirement.
        sys.exit(1)

if __name__ == "__main__":
    # Ensure any uncaught exception is logged before exiting.
    try:
        main()
    except Exception as unexpected:
        logger = get_logger(__name__)
        logger.exception("Unexpected error in error‑handling wrapper.")
        sys.exit(1)