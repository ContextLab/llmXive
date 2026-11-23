"""
Orchestrator for the full download‑clean‑verify pipeline.

This script ties together the individual steps defined in ``code/download.py``:
1. Load the dataset configuration (list of URLs and metadata).
2. Download each dataset to ``data/raw/``.
3. Clean the raw CSV files and write the cleaned versions to ``data/raw/cleaned/``.
4. Compute SHA‑256 checksums for the cleaned files.
5. Record those checksums in ``state/dataset_checksums.yaml``.
6. Verify that the collection contains the required diversity of dataset types
   (numerical‑only, categorical‑only, mixed) using ``code/verify_diversity.py``.

The script can be executed directly::

    python code/orchestrate_download.py

It will log progress to the console and raise any exception that occurs,
causing the pipeline to fail loudly if a step cannot be completed.
"""

import logging
import sys
from pathlib import Path

# Import the public API from the sibling modules as defined in the project
# specification.  All names must match the declared surface.
from download import (
    load_config,
    download_dataset,
    clean_dataset,
    compute_checksum,
    record_checksums,
)
from verify_diversity import verify_dataset_diversity

# Configure a minimal logger – downstream modules also configure logging,
# but we ensure something sensible is present if they are run standalone.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    """
    Execute the end‑to‑end pipeline.

    The function follows the exact order required by tasks T019a‑e:
    load configuration → download → clean → checksum → record → diversity check.
    Any exception raised by the called functions will propagate and abort the
    pipeline, satisfying the “fail loudly” requirement.
    """
    logger.info("Loading dataset configuration")
    config = load_config()

    logger.info("Downloading raw datasets")
    download_dataset(config)

    logger.info("Cleaning downloaded datasets")
    clean_dataset(config)

    logger.info("Computing checksums for cleaned datasets")
    checksums = compute_checksum(config)

    logger.info("Recording checksums to state/dataset_checksums.yaml")
    record_checksums(checksums)

    logger.info("Verifying dataset diversity requirements")
    # The verify_dataset_diversity function is expected to raise an
    # AssertionError (or a custom exception) if the diversity criteria are
    # not met, which will cause the pipeline to fail as required.
    verify_dataset_diversity()

    logger.info("Download‑clean‑verify pipeline completed successfully")


def main(argv: list[str] | None = None) -> int:
    """
    Entry‑point for ``python -m code.orchestrate_download`` or direct execution.

    Returns an exit code compatible with POSIX conventions:
    * ``0`` – success
    * non‑zero – failure (exception details are logged)
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        # The orchestrator does not currently accept command‑line arguments,
        # but the signature allows future extensions without breaking the API.
        run_pipeline()
    except Exception as exc:  # pragma: no cover – exercised by the runner
        logger.exception("Pipeline failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
