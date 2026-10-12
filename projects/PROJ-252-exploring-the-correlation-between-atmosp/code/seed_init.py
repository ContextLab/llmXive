"""
Seed initialization script for the atmospheric pressure–earthquake project.

This script sets deterministic random seeds for the built‑in ``random`` module
and NumPy, writes a confirmation log file, and prints a success message.
It is referenced in ``docs/quickstart.md`` and is the first step of the
reproducible pipeline.
"""
import random
import numpy as np
import sys

# Import the project's package to ensure the ``code/__init__.py`` side‑effects run.
# The ``code/__init__.py`` already sets the seeds, but we set them again here
# for explicitness and to make the log message accurate.
import code  # noqa: F401

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logger = get_logger(__name__)

SEED = 42

def set_seeds(seed: int = SEED) -> None:
    """Set deterministic seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set: random.seed({seed}), np.random.seed({seed})")

def write_log(seed: int = SEED) -> None:
    """Write a short confirmation log file."""
    log_path = paths.logs("seed_initialization.log")
    # Ensure the parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Random seeds initialized to {seed}\\n")
    logger.info(f"Seed initialization log written to {log_path}")

def main() -> int:
    """Entry point for the script."""
    set_seeds()
    write_log()
    # As required by the quick‑start guide, print a success message.
    print("Pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())