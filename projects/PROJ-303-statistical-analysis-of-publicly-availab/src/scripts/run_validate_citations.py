"""
Execute the citation validation script as a blocking gate.

This script runs ``src.scripts.validate_citations.main`` and halts the
pipeline if the validation fails (i.e., a non‑zero exit code is returned).
It logs the outcome using the project's logging configuration.
"""

import sys
from src.scripts.validate_citations import main as validate_main
from src.pipeline.logging_config import get_logger

logger = get_logger(__name__)

def run() -> None:
    """Run the citation validator and exit with the appropriate status."""
    exit_code = validate_main()
    if exit_code != 0:
        logger.error(
            "Citation validation failed. Halting pipeline.",
            {"exit_code": exit_code},
        )
        sys.exit(exit_code)
    else:
        logger.info("Citation validation passed.")
        sys.exit(0)

if __name__ == "__main__":
    run()