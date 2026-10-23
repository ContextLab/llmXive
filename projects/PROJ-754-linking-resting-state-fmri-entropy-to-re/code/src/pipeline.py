"""
pipeline.py
------------
Public orchestrator for the end‑to‑end analysis.

This file has been updated so that all internal imports point to the
correct locations under ``code.src`` and the download stage now uses the
stable ``--subjects`` flag provided by ``code.src.download_data``.
"""

import argparse
import sys
from typing import Any

from llmxive_toolkit import get_logger

# Import the CLI entry points of the individual stages.
from code.src.download_data import main as download_main
from code.src.data.qc import main as qc_main
from code.src.compute_entropy import main as entropy_main


def _run_stage(main_func, argv: list[str]) -> None:
    """
    Helper that temporarily replaces ``sys.argv`` and invokes a stage's
    ``main`` function.
    """
    original_argv = sys.argv
    try:
        sys.argv = argv
        main_func()
    finally:
        sys.argv = original_argv


def run_pipeline(
    subjects: int = 5,
    dry_run: bool = False,
    hcp_token: str | None = None,
    fd_threshold: float = 0.2,
    entropy_r: float = 0.15,
    entropy_m: int = 2,
    scales: tuple[int, ...] = (1, 2, 3, 4, 5),
    batch_size: int = 50,
    **_: Any,
) -> None:
    """
    Execute the full pipeline.

    Parameters
    ----------
    subjects : int
        Number of subjects to process.
    dry_run : bool
        If ``True`` skip all heavy processing (used by the test suite).
    hcp_token : str | None
        Optional HCP access token; if ``None`` the token is read from the
        ``HCP_TOKEN`` environment variable by the download stage.
    fd_threshold : float
        Motion threshold for QC.
    entropy_r, entropy_m, scales, batch_size :
        Parameters forwarded to the entropy stage.
    """
    logger = get_logger(__name__)

    if dry_run:
        logger.info("Dry‑run requested – exiting without processing.")
        return

    # ------------------------------------------------------------------
    # Stage 1 – Download data
    # ------------------------------------------------------------------
    logger.info("Downloading %d subjects.", subjects)
    _run_stage(
        download_main,
        [
            "download_data",
            "--subjects",
            str(subjects),
            "--output-dir",
            "data",
        ],
    )

    # ------------------------------------------------------------------
    # Stage 2 – Quality control
    # ------------------------------------------------------------------
    logger.info("Running quality control.")
    _run_stage(qc_main, ["qc"])

    # ------------------------------------------------------------------
    # Stage 3 – Entropy computation
    # ------------------------------------------------------------------
    logger.info("Computing entropy matrix.")
    _run_stage(
        entropy_main,
        [
            "compute_entropy",
            "--input",
            "data/derived/clean_subjects.parquet",
            "--output",
            "results/entropy_matrix.parquet",
            "--scales",
            *[str(s) for s in scales],
            "--r",
            str(entropy_r),
            "--m",
            str(entropy_m),
            "--batch-size",
            str(batch_size),
        ],
    )

    logger.info("Pipeline completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Programmatic entry point for the pipeline."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Number of subjects to process (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip heavy processing (useful for tests).",
    )
    args = parser.parse_args()
    run_pipeline(subjects=args.subjects, dry_run=args.dry_run)
