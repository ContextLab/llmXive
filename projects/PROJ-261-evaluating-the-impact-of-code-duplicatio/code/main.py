"""
High‑level pipeline orchestration.

The ``run_pipeline`` function stitches together the individual stages:
data download → clone‑density computation → perplexity computation.
It respects the contract expectations of the various helper modules.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from code.data_loader import download_and_save_sample
from code.ast_cloner import compute_clone_density_batch
from code.model_metrics import compute_perplexity_batch  # noqa: F401

logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    """
    Execute the full data‑processing pipeline.

    Steps:
    1. Download a sample of the GitHub code dataset.
    2. Compute clone‑density metrics from the downloaded CSV.
    3. Compute perplexity scores for the same source files.
    """
    # Step 1 – download.
    raw_csv_path = download_and_save_sample()

    # Resolve the directory that contains the raw CSV; downstream stages
    # expect a directory path.
    raw_dir = Path(raw_csv_path).parent

    # Step 2 – compute clone density.
    compute_clone_density_batch(input_path=raw_dir)

    # Step 3 – compute perplexity scores.
    # ``compute_perplexity_batch`` follows the same contract as the clone
    # stage: it receives the directory containing the raw CSV and writes
    # its results to ``data/processed/perplexity_scores.csv``.
    compute_perplexity_batch(input_path=raw_dir)

    logger.info("Pipeline completed successfully.")

def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    """
    Entry point used by ``python -m code.main`` and the quick‑start script.
    Returns an exit code compatible with ``sys.exit``.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        run_pipeline()
        return 0
    except Exception as exc:  # pragma: no cover
        logger.exception("Pipeline failed: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())