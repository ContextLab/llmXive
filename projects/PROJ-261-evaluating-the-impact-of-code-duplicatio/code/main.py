from __future__ import annotations
import logging
from pathlib import Path

# Absolute imports to avoid relative‑import issues when the script is executed directly.
from data_loader import download_and_save_sample
from ast_cloner import compute_clone_density_batch
from model_metrics import compute_perplexity_batch

logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    """
    End‑to‑end pipeline for US‑1:
    1. Download a small sample of the GitHub‑code dataset.
    2. Compute clone‑density metrics.
    3. Compute perplexity scores.
    The resulting CSV files are written to ``data/processed``.
    """
    # Step 1 – download raw data (default sample size)
    download_and_save_sample()

    raw_dir = Path("data/raw")
    # Step 2 – clone density
    compute_clone_density_batch(input_path=raw_dir)

    # Step 3 – perplexity (the implementation lives in ``model_metrics``)
    compute_perplexity_batch(input_path=raw_dir)

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()