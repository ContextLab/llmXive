"""
main.py
-------
Entry point for the end‑to‑end pipeline. This script orchestrates the
following stages:

1. Download a small sample of the ``codeparrot/github-code`` dataset.
2. Compute clone‑density metrics for each Python file.
3. Compute perplexity scores using the 8‑bit ``Salesforce/codegen-350M-mono``
   model.
4. Correlate clone‑density with perplexity and write the results.

All stages write their artefacts to the exact locations expected by
``quickstart_validation.py``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from data_loader import download_and_save_sample
from ast_cloner import compute_clone_density_batch
from model_metrics import compute_perplexity_batch
from correlation_analysis import run_correlation_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    """
    Execute the full pipeline.

    The function is deliberately simple: it triggers the three stages in
    order and relies on each stage to write its own output files.
    """
    # ------------------------------------------------------------------
    # 1. Ensure raw data exists.
    # ------------------------------------------------------------------
    raw_csv = Path("data/raw/github-code-sample.csv")
    if not raw_csv.is_file():
        logger.info("Raw data not found – downloading sample.")
        download_and_save_sample()
    else:
        logger.info("Raw data already present at %s", raw_csv)

    # ------------------------------------------------------------------
    # 2. Compute clone density.
    # ------------------------------------------------------------------
    compute_clone_density_batch()

    # ------------------------------------------------------------------
    # 3. Compute perplexity scores.
    # ------------------------------------------------------------------
    compute_perplexity_batch()

    # ------------------------------------------------------------------
    # 4. Correlate the two metrics.
    # ------------------------------------------------------------------
    run_correlation_analysis()

    logger.info("Pipeline execution completed.")

if __name__ == "__main__":
    run_pipeline()
