"""
run_pipeline_with_logging.py
-----------------------------

Entry‑point script that runs the full analysis pipeline while emitting
comprehensive logs for each major stage (ingestion, preprocessing,
matching/weighting, and validation).  All log messages are written both to
the console and to ``data/logs/pipeline.log`` via the ``logger`` utility
defined in ``code/logger.py``.
"""

import sys
import traceback

# Import the central logger helper
from logger import get_logger

# Import the public ``main`` functions from each pipeline component.
# The public API surface is declared in the project description.
from data.ingestion import main as ingestion_main
from data.preprocessing import main as preprocessing_main
from data.cohort import main as cohort_main
from analysis.validation import main as validation_main

def run_pipeline() -> None:
    """
    Execute the pipeline with detailed logging.

    The function calls the ``main`` entry point of each sub‑module in the
    correct order, logs start/end of each stage, and captures any
    exceptions with a full traceback.  Fallback decisions (e.g., skipping
    the GSS dataset) are expected to be logged by the underlying modules,
    but this wrapper adds high‑level context.
    """
    logger = get_logger(__name__)
    logger.info("=== Pipeline execution started ===")

    # ---------- Ingestion ----------
    logger.info("Starting data ingestion.")
    try:
        ingestion_main()
        logger.info("Data ingestion completed successfully.")
    except Exception as exc:
        logger.error("Data ingestion failed.")
        logger.debug("".join(traceback.format_exception(*sys.exc_info())))
        raise

    # ---------- Preprocessing ----------
    logger.info("Starting preprocessing.")
    try:
        preprocessing_main()
        logger.info("Preprocessing completed successfully.")
    except Exception as exc:
        logger.error("Preprocessing failed.")
        logger.debug("".join(traceback.format_exception(*sys.exc_info())))
        raise

    # ---------- Cohort construction (matching / weighting) ----------
    logger.info("Starting synthetic cohort construction.")
    try:
        cohort_main()
        logger.info("Synthetic cohort construction completed successfully.")
    except Exception as exc:
        logger.error("Cohort construction failed.")
        logger.debug("".join(traceback.format_exception(*sys.exc_info())))
        raise

    # ---------- Validation ----------
    logger.info("Starting synthetic cohort validation.")
    try:
        validation_main()
        logger.info("Synthetic cohort validation completed successfully.")
    except Exception as exc:
        logger.error("Validation failed.")
        logger.debug("".join(traceback.format_exception(*sys.exc_info())))
        raise

    logger.info("=== Pipeline execution finished ===")

if __name__ == "__main__":
    # Running as a script executes the pipeline.
    run_pipeline()
