"""
main.py
-------
Orchestrates the end‑to‑end pipeline for User Story 1:

1. Download a small, real Python corpus.
2. Compute clone‑density metrics.
3. Compute perplexity scores.
4. (Optional) Log parse failures and memory usage.

The script is deliberately lightweight so it can run on CI without GPU
resources.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path

# Absolute imports to avoid relative‑import issues when the script is executed directly.
from data_loader import download_and_save_sample
from ast_cloner import compute_clone_density_batch
from model_metrics import compute_perplexity_batch
from memory_monitor import setup_memory_monitoring

logger = logging.getLogger(__name__)


def run_pipeline() -> int:
    """
    Execute the pipeline.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        # 1. Download a modest sample (default 100 files – fast on CI)
        download_and_save_sample(sample_size=100)

        # 2. Compute clone density
        compute_clone_density_batch()

        # 3. Compute perplexity
        compute_perplexity_batch()

        # 4. Start a background memory monitor (non‑blocking)
        _ = setup_memory_monitoring()

        logger.info("Pipeline completed successfully.")
        return 0
    except Exception as exc:  # pragma: no cover – any unexpected error is logged
        logger.exception("Pipeline failed: %s", exc)
        return 1


if __name__ == "__main__":
    # Configure a very simple root logger for direct script execution.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )
    sys.exit(run_pipeline())