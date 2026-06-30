"""Main pipeline orchestration for the code duplication impact study.

This script orchestrates the end‑to‑end workflow:
1. Download a sample of the ``codeparrot/github-code`` dataset.
2. Compute AST clone‑density metrics.
3. Compute token‑level perplexity scores using the CodeGen model.
4. Write the resulting CSV files to the locations declared in the
   specification.

The script is deliberately tolerant of missing arguments and can be
invoked directly (``python code/main.py``) as part of the quick‑start
run‑book.
"""

import logging
from pathlib import Path

# Import pipeline building blocks
from data_loader import download_and_save_sample
from ast_cloner import compute_clone_density_batch
from model_metrics import compute_perplexity_batch
from memory_monitor import (
    setup_memory_monitoring,
    start_memory_monitoring,
    stop_memory_monitoring,
)

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def _setup_logging() -> logging.Logger:
    """Configure a simple console logger and return it."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Core pipeline
# ----------------------------------------------------------------------
def run_pipeline(
    raw_csv_path: Path,
    clone_csv_path: Path,
    perplexity_csv_path: Path,
    max_samples: int = 1000,
) -> None:
    """Execute the three‑stage pipeline.

    Parameters
    ----------
    raw_csv_path: Path
        Destination for the raw ``github-code`` CSV sample.
    clone_csv_path: Path
        Destination for the clone‑density CSV.
    perplexity_csv_path: Path
        Destination for the perplexity‑scores CSV.
    max_samples: int, optional
        Upper bound on the number of examples to download. The default
        (1000) keeps the run‑book lightweight while still providing a
        meaningful sample.
    """
    logger = _setup_logging()
    logger.info("Starting pipeline execution")

    # ------------------------------------------------------------------
    # Stage 1 – download raw data (if not already present)
    # ------------------------------------------------------------------
    if not raw_csv_path.is_file():
        logger.info("Downloading raw dataset to %s", raw_csv_path)
        download_and_save_sample(
            output_path=str(raw_csv_path),
            max_samples=max_samples,
        )
    else:
        logger.info("Raw dataset already exists at %s – skipping download", raw_csv_path)

    # ------------------------------------------------------------------
    # Stage 2 – clone density computation
    # ------------------------------------------------------------------
    logger.info("Computing clone‑density metrics")
    compute_clone_density_batch(
        input_path=str(raw_csv_path),
        output_path=str(clone_csv_path),
    )
    logger.info("Clone‑density metrics written to %s", clone_csv_path)

    # ------------------------------------------------------------------
    # Stage 3 – perplexity computation
    # ------------------------------------------------------------------
    logger.info("Computing perplexity scores")
    compute_perplexity_batch(
        input_path=str(raw_csv_path),
        output_path=str(perplexity_csv_path),
    )
    logger.info("Perplexity scores written to %s", perplexity_csv_path)

    logger.info("Pipeline completed successfully")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """CLI entry point used by the quick‑start run‑book."""
    # Initialise optional memory monitoring (the function is tolerant of
    # missing arguments – see the patch in ``memory_monitor.py``).
    try:
        setup_memory_monitoring()
    except Exception as exc:  # pragma: no cover – defensive
        logging.getLogger(__name__).warning(
            "Memory‑monitoring initialisation failed: %s", exc
        )

    # Start background memory monitor (if the implementation supports it)
    try:
        start_memory_monitoring()
    except Exception:  # pragma: no cover – defensive
        pass

    try:
        # Resolve all required paths
        raw_path = Path("data/raw/github-code-sample.csv")
        clone_path = Path("data/processed/clone_metrics.csv")
        perplexity_path = Path("data/processed/perplexity_scores.csv")

        # Ensure destination directories exist
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        clone_path.parent.mkdir(parents=True, exist_ok=True)
        perplexity_path.parent.mkdir(parents=True, exist_ok=True)

        run_pipeline(
            raw_csv_path=raw_path,
            clone_csv_path=clone_path,
            perplexity_csv_path=perplexity_path,
        )
    finally:
        # Gracefully stop the monitor regardless of success/failure.
        try:
            stop_memory_monitoring()
        except Exception:  # pragma: no cover – defensive
            pass

if __name__ == "__main__":
    main()
