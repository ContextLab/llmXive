from __future__ import annotations
import logging
from pathlib import Path

from correlation_analysis import main as correlation_main

logger = logging.getLogger(__name__)

def main() -> None:
    """
    Wrapper script invoked by the quickstart run‑book.  It simply forwards
    to ``correlation_analysis.main`` which writes the required CSV file.
    """
    logger.info("Generating correlation results...")
    correlation_main()
    logger.info("Correlation generation complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
