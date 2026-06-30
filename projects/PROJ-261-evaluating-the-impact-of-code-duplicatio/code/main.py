"""Top‑level pipeline orchestration.

This script is the entry point used by the quick‑start run‑book
(``python code/main.py``).  It now uses absolute imports so that it can be
executed as a script without being part of a package.
"""

import logging
from pathlib import Path

# Absolute imports – required when the module is run as ``__main__``.
from code.data_loader import download_and_save_sample
from code.ast_cloner import compute_clone_density_batch
from code.memory_monitor import setup_memory_monitoring, memory_monitor_context
from code.model_metrics import main as run_model_metrics

logger = logging.getLogger(__name__)

def run_pipeline() -> None:
    """Execute the full US‑1 pipeline.

    1. Download a sample of the GitHub‑code dataset.
    2. Scan for PII (handled in a separate task – already executed elsewhere).
    3. Compute clone density.
    4. Run the model‑metrics step (perplexity).
    """
    # Step 1 – download data.
    raw_csv_path = download_and_save_sample()

    # Step 2 – (PII scan is performed by a separate script; we just log).
    logger.info("Data downloaded to %s", raw_csv_path)

    # Step 3 – compute clone density.
    raw_dir = Path("data/raw")
    compute_clone_density_batch(input_path=raw_dir)

    # Step 4 – run model‑metrics (perplexity computation).
    run_model_metrics()

def main() -> None:
    """Entry point for ``python code/main.py``."""
    # Initialise a memory monitor to respect the 7 GB limit.
    setup_memory_monitoring()
    with memory_monitor_context():
        run_pipeline()

if __name__ == "__main__":
    # Configure a basic logger for ad‑hoc runs.
    logging.basicConfig(level=logging.INFO)
    main()
