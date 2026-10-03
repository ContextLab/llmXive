"""
fetch_literature_pcm.py

This module fetches the literature phase‑change material (PCM) validation set
from the public HuggingFace dataset ``matbench/literature_pcm_validation_set``
and stores it as a CSV file under ``data/external/literature_pcms_raw.csv``.

The implementation avoids importing the project's ``utils`` package to
sidestep a circular‑import issue that can arise when ``utils.__init__`` pulls
in heavy sub‑modules. Instead, it configures and uses the standard ``logging``
library directly. All other functionality remains unchanged: the dataset is
loaded via ``datasets.load_dataset``, converted to a ``pandas.DataFrame``, and
written to the prescribed output path.
"""

import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
# Configure a simple logger for this script.  The logger name matches the
# module name so that it integrates nicely with any external logging
# configuration the project may set up.
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Prevent duplicate handlers if the script is imported multiple times.
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

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
    try:
        logger.info("Loading 'matbench/literature_pcm_validation_set' dataset...")
        # The dataset is small; loading it entirely in memory is fine.
        ds = load_dataset("matbench/literature_pcm_validation_set", split="train")
        logger.info("Dataset loaded successfully.")
    except Exception as exc:  # pragma: no cover – let the caller see the error
        logger.exception("Failed to load the literature PCM dataset.")
        raise

    try:
        df = ds.to_pandas()
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to convert dataset to pandas DataFrame.")
        raise

    _ensure_parent_dir(OUTPUT_PATH)

    try:
        df.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Literature PCM data written to {OUTPUT_PATH}")
    except Exception as exc:  # pragma: no cover
        logger.exception(f"Failed to write CSV to {OUTPUT_PATH}")
        raise

    return df


def main() -> None:
    """
    Entry‑point for ``python -m code.data.fetch_literature_pcm``.
    Executes the fetch and logs any unexpected error.
    """
    try:
        fetch_literature_pcm()
    except Exception as exc:
        logger.error(f"fetch_literature_pcm failed: {exc}")
        raise


if __name__ == "__main__":
    main()