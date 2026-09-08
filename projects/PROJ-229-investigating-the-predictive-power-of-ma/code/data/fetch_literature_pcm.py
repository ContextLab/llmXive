"""
fetch_literature_pcm.py

This module fetches the literature phase‑change material (PCM) validation set
from the public HuggingFace dataset ``matbench/literature_pcm_validation_set``
and stores it as a CSV file under ``data/external/literature_pcms_raw.csv``.
The script is deliberately lightweight: it loads the dataset (streaming is not
required because the validation set is small), converts it to a ``pandas``
DataFrame and writes the CSV.  All logging is performed through the project's
unified logger obtained via ``utils.logger.get_pipeline_logger``.
"""

import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from utils.logger import get_pipeline_logger, log_info, log_error

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OUTPUT_PATH = Path("data/external/literature_pcms_raw.csv")


def _ensure_parent_dir(path: Path) -> None:
    """Make sure the parent directory of *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def fetch_literature_pcm() -> pd.DataFrame:
    """
    Fetch the literature PCM validation set from the ``matbench`` HuggingFace
    repository and write it to ``OUTPUT_PATH`` as a CSV file.

    Returns
    -------
    pandas.DataFrame
        The loaded validation set.
    """
    logger = get_pipeline_logger(__name__)

    try:
        logger.info("Loading 'matbench/literature_pcm_validation_set' dataset...")
        # The dataset is small; loading it entirely in memory is fine.
        ds = load_dataset("matbench/literature_pcm_validation_set", split="train")
        logger.info("Dataset loaded successfully.")
    except Exception as exc:
        logger.exception("Failed to load the literature PCM dataset.")
        raise

    # Convert to pandas for easy CSV export.
    try:
        df = ds.to_pandas()
    except Exception as exc:
        logger.exception("Failed to convert dataset to pandas DataFrame.")
        raise

    # Ensure output directory exists.
    _ensure_parent_dir(OUTPUT_PATH)

    try:
        df.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Literature PCM data written to {OUTPUT_PATH}")
    except Exception as exc:
        logger.exception(f"Failed to write CSV to {OUTPUT_PATH}")
        raise

    return df


def main() -> None:
    """
    Entry‑point for ``python -m code.data.fetch_literature_pcm``.
    Executes the fetch and logs any unexpected error.
    """
    logger = get_pipeline_logger(__name__)
    try:
        fetch_literature_pcm()
    except Exception as exc:
        logger.error(f"fetch_literature_pcm failed: {exc}")
        raise


if __name__ == "__main__":
    main()