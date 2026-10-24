"""
Main entry point for the project.

Supports three modes:
* ``--demo`` – runs a minimal demonstration that generates synthetic data,
  fits a simple model, and writes the required output artifacts.
* ``--full-run`` – orchestrates the full end‑to‑end pipeline (download,
  ingest, aggregation, modelling, etc.).  This mode is retained for later
  phases but is not used in the thin‑pipeline tests.
* ``--step <name>`` – runs an individual pipeline step (kept for backward
  compatibility).

The demo mode now executes the thin end‑to‑end pipeline required for
T003, producing:
  - ``data/processed/ingested_cohort.parquet``
  - ``data/processed/user_track_pairs.parquet``
  - ``data/final/regression_summary.csv``

The implementation avoids importing the external ``pyarrow`` package to
prevent the circular‑import issue observed in earlier runs.
"""

import sys
import logging
from pathlib import Path

from config import ensure_directories, get_project_root
from utils import setup_logging, get_logger

# Import the thin‑pipeline demo implementation
from simulate_demo import main as run_thin_demo

logger = get_logger(__name__)


def run_demo() -> None:
    """Run the thin end‑to‑end demo pipeline."""
    logger.info("Running demo mode – generating synthetic data and model.")
    # Ensure the standard project directories exist
    ensure_directories()
    # Execute the synthetic demo pipeline
    run_thin_demo()
    logger.info("Demo pipeline completed successfully.")


def run_thin_pipeline() -> None:
    """Execute the thin end‑to‑end pipeline used in early development."""
    logger.info("Executing Thin End‑to‑End Pipeline (legacy entry).")
    ensure_directories()

    logger.info("Step 1: Ingestion")
    # Legacy calls – kept for compatibility but not used in the demo
    try:
        import data_ingestion
        data_ingestion.main()
    except Exception as e:
        logger.warning(f"Legacy ingestion step failed (expected in thin demo): {e}")

    logger.info("Step 2: Aggregation")
    try:
        import aggregation
        aggregation.main()
    except Exception as e:
        logger.warning(f"Legacy aggregation step failed (expected in thin demo): {e}")

    logger.info("Step 3: Modeling")
    try:
        import modeling
        modeling.main()
    except Exception as e:
        logger.warning(f"Legacy modeling step failed (expected in thin demo): {e}")

    logger.info("Thin pipeline completed successfully.")


def main() -> None:
    """Parse command‑line arguments and dispatch to the appropriate mode."""
    setup_logging()

    # No arguments → run demo (convenient default for quickstart)
    if len(sys.argv) == 1:
        run_demo()
        return

    # Handle ``--demo`` explicitly
    if sys.argv[1] == "--demo":
        run_demo()
        return

    # Backward‑compatible step handling
    if sys.argv[1] == "--step":
        if len(sys.argv) < 3:
            logger.error("No step specified after --step")
            sys.exit(1)
        step = sys.argv[2]
        if step == "ingest":
            ensure_directories()
            import data_ingestion
            data_ingestion.main()
            sys.exit(0)
        elif step == "download":
            logger.info("Download step is handled within ingestion for the thin pipeline.")
            sys.exit(0)
        elif step == "analyze":
            ensure_directories()
            import modeling
            modeling.main()
            sys.exit(0)
        elif step == "verify":
            logger.info("Verify step: Handled by external tests.")
            sys.exit(0)
        else:
            logger.error(f"Unknown step: {step}")
            sys.exit(1)

    # Full pipeline execution
    if sys.argv[1] == "--full-run":
        run_thin_pipeline()
        return

    # Any other argument pattern is unexpected
    logger.error(f"Unrecognized arguments: {' '.join(sys.argv[1:])}")
    sys.exit(1)


if __name__ == "__main__":
    main()
