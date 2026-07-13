"""
Small wrapper that forwards the ``main`` call to the concrete implementation
in ``code.analysis.correlations``. The original version attempted to import
``analysis.correlation_main_runner`` (a non‑existent module) which caused a
``ModuleNotFoundError`` and prevented the entire pipeline from executing.
This file now correctly imports the ``main`` function from the
``code.analysis.correlations`` module and exposes it under the expected name.
"""

import logging
from code.analysis import correlations

logger = logging.getLogger(__name__)

def main() -> None:
    """
    Entry point used by ``code/main.py``. Delegates to
    ``code.analysis.correlations.main`` which performs the full analysis
    workflow (loading metrics, PCA, merging, and saving outputs).
    """
    logger.info("Running correlation_main_runner")
    correlations.main()