"""Create the `results/` directory (idempotent) and verify write access.

This script follows the same pattern as the other directory‑creation utilities
(e.g., `create_code_dir.py`, `create_tests_dir.py`). It can be run multiple
times without error and will raise an exception if the resulting directory is
not writable.
"""

import os
from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def create_and_verify_results_dir() -> Path:
    """Create the `results/` directory if it does not exist and verify writability.

    Returns
    -------
    Path
        Absolute path to the created (or already existing) ``results`` directory.
    """
    # The project root is the current working directory when the script is invoked.
    results_dir = Path.cwd() / "results"

    # Create the directory idempotently.
    results_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"Ensured results directory exists at {results_dir}")

    # Verify that the directory is writable.
    if not os.access(results_dir, os.W_OK):
        raise PermissionError(f"The results directory '{results_dir}' is not writable.")
    log.debug(f"Write access confirmed for results directory {results_dir}")

    return results_dir

if __name__ == "__main__":
    try:
        path = create_and_verify_results_dir()
        print(f"Results directory ready at: {path}")
    except Exception as exc:
        log.error(f"Failed to create or verify results directory: {exc}")
        raise
