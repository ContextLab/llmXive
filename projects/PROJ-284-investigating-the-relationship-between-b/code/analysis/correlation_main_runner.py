"""
Entry‑point wrapper used by ``code/main.py`` to run the correlation
analysis pipeline.

The original file attempted to import from a non‑existent top‑level
``analysis`` package which caused ``ModuleNotFoundError`` during the
quick‑start run‑book.  This rewritten version simply forwards the call
to the real ``correlations.main`` implementation inside the same package.
"""

import logging
from pathlib import Path

# Import the real implementation from the sibling module.
from code.analysis.correlations import main as _correlations_main

__all__ = ["main"]

def main() -> None:
    """Run the full correlation analysis pipeline."""
    logger = logging.getLogger(__name__)
    logger.info("Starting correlation analysis via correlation_main_runner")
    _correlations_main()
    logger.info("Correlation analysis completed")
