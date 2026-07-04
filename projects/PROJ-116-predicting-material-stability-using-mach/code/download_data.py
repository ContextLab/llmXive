"""download_data.py
-----------------
Fetch the OQMD dataset, filter for Li‑rich rock‑salt structures, and
save the filtered data to the project's raw data directory.

The script is intended to be run directly:
    python code/download_data.py

It logs a warning if the number of filtered samples is below a
predefined threshold.
"""

from pathlib import Path
import logging

import pandas as pd
from pymatgen.core import Composition
from matminer.datasets import load_dataset

# Local imports
from utils.logging import setup_logger


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MIN_SAMPLE_THRESHOLD = 100  # Minimum acceptable number of filtered rows

# Resolve the project root (two levels up from this file) and the raw data dir
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DATA_DIR / "oqmd_li_rocksalt.csv"


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def is_li_rich(composition_str: str) -> bool:
    """
    Return True if the composition contains lithium.
    """
    try:
        comp = Composition(composition_str)
        return "Li" in comp.as_dict()
    except Exception:  # pragma: no cover
        return False


def is_rocksalt(spacegroup) -> bool:
    """
    Rock‑salt structures are typically in space group 225 (Fm-3m).
    """
    try:
        return int(spacegroup) == 225
    except Exception:  # pragma: no cover
        return False


# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    logger: logging.Logger = setup_logger(__name__)
    logger.info("Starting OQMD data download via matminer.")

    # Load the full OQMD dataset
    try:
        df = load_dataset("oqmd")
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to load OQMD dataset: {exc}")
        raise

    logger.info(f"OQMD dataset loaded with {len(df)} total entries.")

    # Ensure required columns exist
    required_cols = {"composition", "spacegroup"}
    missing = required_cols - set(df.columns)
    if missing:
        logger.error(f"Missing expected columns in OQMD dataset: {missing}")
        raise RuntimeError("Dataset does not contain required columns.")

    # Apply filters
    mask_li = df["composition"].apply(is_li_rich)
    mask_rs = df["spacegroup"].apply(is_rocksalt)
    filtered_df = df[mask_li & mask_rs].copy()

    logger.info(
        f"Filtered dataset contains {len(filtered_df)} Li‑rich rock‑salt entries."
    )

    if len(filtered_df) < MIN_SAMPLE_THRESHOLD:
        logger.warning(
            f"Number of filtered samples ({len(filtered_df)}) is below the "
            f"threshold of {MIN_SAMPLE_THRESHOLD}."
        )

    # Save filtered data
    try:
        filtered_df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Filtered data saved to {OUTPUT_FILE}")
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to write filtered data: {exc}")
        raise


if __name__ == "__main__":
    main()
