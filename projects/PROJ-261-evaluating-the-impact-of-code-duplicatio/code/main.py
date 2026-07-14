"""main.py
Orchestrates the full pipeline. Updated to call the newly tolerant
functions and to verify that the required CSV artefacts are produced.
"""
from __future__ import annotations

import logging
from pathlib import Path

from data_loader import download_and_save_sample
from ast_cloner import compute_clone_density_batch
from model_metrics import compute_perplexity_batch
from bug_detection import main as bug_detection_main

logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)


def _ensure_output(path: Path) -> None:
    """Utility used by the pipeline to assert that a file exists."""
    if not path.is_file():
        raise FileNotFoundError(f"Pipeline expected output not found: {path}")


def run_pipeline() -> None:
    """
    End‑to‑end pipeline:
    1. Download a small, reproducible sample.
    2. Compute clone‑density metrics.
    3. Compute surrogate perplexity scores.
    4. Run the bug‑detection step (produces its own artefacts).
    5. Verify that the two core CSV files exist.
    """
    # Step 1: download a small sample (used by downstream steps)
    download_and_save_sample(sample_size=100)

    # Step 2: compute clone density
    compute_clone_density_batch()

    # Step 3: compute perplexity (implementation unchanged)
    compute_perplexity_batch()

    # Step 4: bug detection & pass@1
    bug_detection_main()

    # Verify that the artefacts required by quickstart_validation exist
    _ensure_output(Path("data/processed/clone_metrics.csv"))
    _ensure_output(Path("data/processed/perplexity_scores.csv"))

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()