from __future__ import annotations
import logging
from pathlib import Path

from correlation_analysis import run_correlation_analysis

logger = logging.getLogger(__name__)

def main() -> None:
    """
    Wrapper entry‑point used by ``code/main.py`` and the quick‑start run‑book.
    It simply forwards to the full correlation analysis routine.
    """
    logger.info("Running correlation analysis")
    run_correlation_analysis()
    logger.info("Correlation analysis finished")

if __name__ == "__main__":
    main()
