from __future__ import annotations

"""
split_dataset.py

This module provides utilities to perform a project‑level stratified train/test
split of the processed dataset, write the resulting splits to disk, document the
split proportions, and **validate that each project appears in only one split**.

Public API
----------
- get_split_proportions() -> Tuple[float, float]
    Returns the (train_fraction, test_fraction) used for the split.
- document_split_proportions(output_path: Path) -> None
    Writes a JSON file describing the split proportions.
- main() -> None
    CLI entry point: loads the processed dataset, creates the split, validates
    uniqueness of project assignment, and persists the results.
"""

import json
import os
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

# Local utilities
from utils.config import get_seed, set_random_seed, Config
from utils.logging import get_logger

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Default split fractions – can be overridden via environment variables if
# desired (e.g. for experimentation).  The task description specifies a
# deferred 30 % test split.
DEFAULT_TRAIN_FRAC: float = 0.70
DEFAULT_TEST_FRAC: float = 0.30

# Project‑root ``data`` directory (relative to this file's location)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "dataset.csv"

SPLIT_OUTPUT_DIR = DATA_DIR / "splits"
TRAIN_OUTPUT_PATH = SPLIT_OUTPUT_DIR / "train.csv"
TEST_OUTPUT_PATH = SPLIT_OUTPUT_DIR / "test.csv"
PROPORTIONS_OUTPUT_PATH = SPLIT_OUTPUT_DIR / "split_proportions.json"

logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def get_split_proportions() -> Tuple[float, float]:
    """
    Return the train / test split fractions.

    The fractions can be overridden by the environment variables
    ``TRAIN_FRAC`` and ``TEST_FRAC``.  If only one of them is set, the other
    is inferred so that the two sum to 1.0.

    Returns
    -------
    Tuple[float, float]
        (train_fraction, test_fraction)
    """
    train_frac = float(os.getenv("TRAIN_FRAC", DEFAULT_TRAIN_FRAC))
    test_frac = float(os.getenv("TEST_FRAC", DEFAULT_TEST_FRAC))

    # Ensure they sum to 1.0 – if not, normalise.
    total = train_frac + test_frac
    if not abs(total - 1.0) < 1e-6:
        logger.warning(
            "Train and test fractions do not sum to 1.0 (got %s). Normalising.",
            total,
        )
        train_frac = train_frac / total
        test_frac = test_frac / total

    return train_frac, test_frac


def document_split_proportions(output_path: Path) -> None:
    """
    Persist the split proportions to a JSON file.

    Parameters
    ----------
    output_path: Path
        Destination file path (parents are created if missing).
    """
    train_frac, test_frac = get_split_proportions()
    data = {"train_fraction": train_frac, "test_fraction": test_frac}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Documented split proportions at %s", output_path)


def _validate_project_uniqueness(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """
    Assert that each project appears in only one of the two splits.

    Parameters
    ----------
    train_df: pd.DataFrame
        Training split.
    test_df: pd.DataFrame
        Testing split.

    Raises
    ------
    AssertionError
        If any project identifier is present in both splits.
    """
    if "project" not in train_df.columns or "project" not in test_df.columns:
        raise AssertionError(
            "Both train and test DataFrames must contain a 'project' column for validation."
        )

    train_projects = set(train_df["project"].unique())
    test_projects = set(test_df["project"].unique())
    overlap = train_projects.intersection(test_projects)

    if overlap:
        raise AssertionError(
            f"Projects appear in both train and test splits: {sorted(overlap)}"
        )
    logger.debug("Project uniqueness validation passed – no overlap found.")


# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Execute the full split pipeline:
    1. Load the processed dataset.
    2. Perform a stratified split on the ``project`` column.
    3. Validate that each project is assigned to a single split.
    4. Write the train / test CSV files.
    5. Document the split proportions.
    """
    # ------------------------------------------------------------------- #
    # 0. Seed handling – reproducibility across runs
    # ------------------------------------------------------------------- #
    seed = get_seed()
    set_random_seed(seed)
    logger.info("Using random seed %s for train/test split.", seed)

    # ------------------------------------------------------------------- #
    # 1. Load dataset
    # ------------------------------------------------------------------- #
    if not PROCESSED_DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Processed dataset not found at {PROCESSED_DATA_PATH}. "
            "Run the data pipeline to generate it first."
        )
    df = pd.read_csv(PROCESSED_DATA_PATH)
    logger.info("Loaded processed dataset with %d rows and %d columns.", df.shape[0], df.shape[1])

    # ------------------------------------------------------------------- #
    # 2. Perform stratified split on 'project'
    # ------------------------------------------------------------------- #
    if "project" not in df.columns:
        raise KeyError("Column 'project' is required in the dataset for stratified splitting.")

    train_frac, test_frac = get_split_proportions()
    # sklearn's train_test_split uses ``test_size``; we compute it directly.
    train_df, test_df = train_test_split(
        df,
        test_size=test_frac,
        stratify=df["project"],
        random_state=seed,
    )
    logger.info(
        "Created train split with %d rows and test split with %d rows.",
        train_df.shape[0],
        test_df.shape[0],
    )

    # ------------------------------------------------------------------- #
    # 3. Validation – each project appears in only one split
    # ------------------------------------------------------------------- #
    _validate_project_uniqueness(train_df, test_df)

    # ------------------------------------------------------------------- #
    # 4. Persist splits
    # ------------------------------------------------------------------- #
    SPLIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(TRAIN_OUTPUT_PATH, index=False)
    test_df.to_csv(TEST_OUTPUT_PATH, index=False)
    logger.info("Saved train split to %s", TRAIN_OUTPUT_PATH)
    logger.info("Saved test split to %s", TEST_OUTPUT_PATH)

    # ------------------------------------------------------------------- #
    # 5. Document proportions
    # ------------------------------------------------------------------- #
    document_split_proportions(PROPORTIONS_OUTPUT_PATH)

    logger.info("Dataset split pipeline completed successfully.")


if __name__ == "__main__":
    main()