"""
Top‑level orchestration script for the HEA elastic‑modulus pipeline.

The ``--stage`` command‑line argument selects which part of the pipeline
to run.  For the purpose of task **T002** we implement the ``fetch``
stage, which delegates to :pymod:`code.data.fetch` and records provenance
metadata.
"""

import argparse
import logging
import sys

from code.data.fetch import fetch_all
from code.utils.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def _stage_fetch() -> None:
    """
    Execute the data‑ingestion stage.

    This function calls :func:`code.data.fetch.fetch_all`, which handles
    retrieval from the Materials Project and OQMD, writes raw dumps to
    ``data/raw/``, and generates ``data/source_metadata.yaml``.
    """
    logger.info("Starting FETCH stage.")
    fetch_all()
    logger.info("FETCH stage completed successfully.")


# ----------------------------------------------------------------------
# Placeholder stubs for other stages (required for CLI completeness)
# ----------------------------------------------------------------------
def _stage_engineer() -> None:
    logger.info("ENGINEER stage not implemented in this task.")
    # In a full implementation this would invoke feature‑engineering code.


def _stage_train() -> None:
    logger.info("TRAIN stage not implemented in this task.")
    # In a full implementation this would train regression models.


def _stage_report() -> None:
    logger.info("REPORT stage not implemented in this task.")
    # In a full implementation this would generate the final report.


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: list | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="HEA Elastic Modulus Prediction Pipeline"
    )
    parser.add_argument(
        "--stage",
        choices=["fetch", "engineer", "train", "report", "all"],
        required=True,
        help="Pipeline stage to execute.",
    )
    args = parser.parse_args(argv)

    # Initialise logging – default INFO level; can be overridden by env vars
    setup_logging(level="INFO")

    if args.stage == "fetch":
        _stage_fetch()
    elif args.stage == "engineer":
        _stage_engineer()
    elif args.stage == "train":
        _stage_train()
    elif args.stage == "report":
        _stage_report()
    elif args.stage == "all":
        _stage_fetch()
        _stage_engineer()
        _stage_train()
        _stage_report()
    else:
        logger.error("Unknown stage: %s", args.stage)
        sys.exit(1)


if __name__ == "__main__":
    main()
