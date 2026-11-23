"""
main.py
--------

Minimal orchestrator required for the quick‑start command
``python code/main.py``.  It runs the specification validation step
(Task T001) and the WDPA site‑metadata acquisition step (Task T003).
"""

import sys
import logging

from code.spec_validation import main as spec_validation_main
from fetch_site_coordinates import main as fetch_sites_main

def _setup_root_logger() -> None:
    """Configure a simple root logger for the orchestrator."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def run_pipeline() -> int:
    """
    Execute the two core validation / data‑acquisition steps.
    Returns ``0`` on success, non‑zero on failure (mirroring the
    behaviour expected by the quick‑start script).
    """
    _setup_root_logger()
    try:
        logging.info("Running specification validation (T001)…")
        spec_validation_main()
        logging.info("Specification validation succeeded.")
    except Exception as exc:
        logging.error(f"Specification validation failed: {exc}")
        return 1

    try:
        logging.info("Fetching site coordinates (T003)…")
        fetch_sites_main()
        logging.info("Site‑metadata acquisition succeeded.")
    except Exception as exc:
        logging.error(f"Site‑metadata acquisition failed: {exc}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(run_pipeline())
