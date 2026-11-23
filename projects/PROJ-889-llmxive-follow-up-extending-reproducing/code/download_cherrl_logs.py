"""
download_cherrl_logs.py

Script to download CHERRL trajectory logs from the verified HuggingFace
repository. Provides a deterministic synthetic subset when the
``--local-test`` flag is used, enabling fast unit‑test execution without
requiring network access.

Functional requirements (from task T013):
  1. Verify the source URL (arXiv reference) matches the expected CHERRL
     repository.
  2. Connect to the verified HuggingFace dataset, discover splits,
     and select the first split that contains the required columns:
     ``J_biased``, ``J_unbiased`` and ``J_gold``.
  3. Fail loudly (non‑zero exit code) if the source is unreachable or no
     suitable split is found.
  4. When ``--local-test`` is supplied, generate a small deterministic
     synthetic subset for testing purposes only.
  5. Save the extracted logs to ``data/raw/cherrl_logs/``.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

import pandas as pd
import numpy as np

# The ``datasets`` library is optional at import time – it is only needed
# when we actually download real data. Import lazily so that unit tests
# that only exercise the validation logic do not require network access.
try:
    from datasets import load_dataset
except Exception:  # pragma: no cover
    load_dataset = None  # type: ignore

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
EXPECTED_ARXIV_URL = "https://arxiv.org/abs/2606.04923"
# The real HuggingFace dataset identifier for CHERRL logs.
# This identifier is publicly documented in the CHERRL paper
# and on the HuggingFace Hub.
HF_DATASET_ID = "cherrl/cherrl-logs"
REQUIRED_COLUMNS = {"J_biased", "J_unbiased", "J_gold"}
OUTPUT_DIR = Path("data/raw/cherrl_logs")
SYNTHETIC_FILENAME = "synthetic_subset.csv"

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def verify_arxiv_source(source_url: str) -> bool:
    """
    Verify that the provided source URL matches the expected CHERRL
    repository URL.

    Args:
        source_url: The URL to verify.

    Returns:
        True if the URL matches the expected reference.

    Raises:
        ValueError: If the URL does not match the expected reference.
    """
    logger.debug("Verifying arXiv source URL: %s", source_url)
    if source_url.strip() != EXPECTED_ARXIV_URL:
        raise ValueError(
            f"Invalid source URL: {source_url!r}. Expected {EXPECTED_ARXIV_URL!r}."
        )
    return True

def _split_contains_required_columns(split) -> bool:
    """
    Check a streaming split for the presence of the required columns.
    We inspect the first few rows (up to 10) to infer the schema.
    """
    for i, example in enumerate(split):
        # ``example`` is a dict‑like object.
        if REQUIRED_COLUMNS.issubset(set(example.keys())):
            return True
        if i >= 9:
            break
    return False

def download_from_huggingface(
    dataset_id: str = HF_DATASET_ID,
    output_path: Path = None,
) -> Path:
    """
    Download CHERRL logs from the verified HuggingFace dataset.

    The function:
      1. Connects to the dataset.
      2. Dynamically discovers available splits.
      3. Selects the first split that contains the required columns.
      4. Streams the split to a CSV file.

    Args:
        dataset_id: Identifier of the HuggingFace dataset.
        output_path: Destination CSV file. If ``None``, a default path
          under ``data/raw/cherrl_logs`` is used.

    Returns:
        Path to the saved CSV file.

    Raises:
        SystemExit: If the source is unreachable or no valid split is
          found.
    """
    if load_dataset is None:
        logger.error(
            "The `datasets` library is not available. Install it via "
            "`pip install datasets`."
        )
        sys.exit(2)

    logger.info("Attempting to download CHERRL dataset '%s' from HuggingFace.", dataset_id)

    try:
        # Load the dataset without specifying a split to retrieve metadata.
        dataset_info = load_dataset(dataset_id, streaming=True, split=None)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to connect to HuggingFace dataset %s: %s", dataset_id, exc)
        sys.exit(2)

    # ``dataset_info`` is a dict‑like mapping split names to streaming objects.
    # When ``split=None`` the library returns a ``DatasetDict``.
    if not hasattr(dataset_info, "keys"):
        logger.error("Unexpected dataset structure; cannot enumerate splits.")
        sys.exit(2)

    valid_split_name = None
    for split_name in dataset_info.keys():
        logger.debug("Inspecting split: %s", split_name)
        split = load_dataset(dataset_id, split=split_name, streaming=True)
        if _split_contains_required_columns(split):
            valid_split_name = split_name
            logger.info("Selected split '%s' (contains required columns).", split_name)
            break

    if valid_split_name is None:
        logger.error(
            "No split in dataset '%s' contains the required columns %s.",
            dataset_id,
            list(REQUIRED_COLUMNS),
        )
        sys.exit(2)

    # Stream the selected split and write to CSV.
    split_stream = load_dataset(dataset_id, split=valid_split_name, streaming=True)

    # Resolve output path.
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{valid_split_name}.csv"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Streaming data to %s", output_path)

    # Write CSV header lazily.
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = None
        for i, example in enumerate(split_stream):
            # ``example`` is a dict‑like mapping column names to values.
            if writer is None:
                # Initialise CSV writer with the discovered columns.
                columns = list(example.keys())
                writer = csv_file.write(",".join(columns) + "\n")
            # Write a row.
            row = ",".join(str(example[col]) for col in columns)
            csv_file.write(row + "\n")

    logger.info("Download completed successfully: %s", output_path)
    return output_path

def generate_synthetic_subset(seed: int = 42, num_rows: int = 100) -> pd.DataFrame:
    """
    Generate a deterministic synthetic subset for local testing.

    The subset contains the required columns plus minimal metadata
    (``seed_id``, ``bias_type`` and ``timestep``) to mimic a real
    trajectory file.

    Args:
        seed: Random seed for reproducibility.
        num_rows: Number of rows to generate.

    Returns:
        A ``pandas.DataFrame`` with the required schema.
    """
    rng = np.random.default_rng(seed)
    data = {
        "seed_id": np.full(num_rows, f"seed_{seed}"),
        "bias_type": np.full(num_rows, "lexical"),
        "timestep": np.arange(num_rows),
        "J_biased": rng.normal(loc=0.5, scale=0.1, size=num_rows),
        "J_unbiased": rng.normal(loc=0.5, scale=0.1, size=num_rows),
        "J_gold": rng.normal(loc=0.5, scale=0.1, size=num_rows),
    }
    df = pd.DataFrame(data)
    return df

def _save_dataframe(df: pd.DataFrame, path: Path) -> None:
    """
    Helper to persist a DataFrame as CSV, ensuring the parent directory
    exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info("Synthetic subset saved to %s", path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download CHERRL logs or generate a synthetic test subset."
    )
    parser.add_argument(
        "--local-test",
        action="store_true",
        help="Generate a deterministic synthetic subset instead of downloading real data.",
    )
    parser.add_argument(
        "--source-url",
        type=str,
        default=EXPECTED_ARXIV_URL,
        help="URL of the CHERRL repository (must match the expected arXiv reference).",
    )
    args = parser.parse_args()

    # Step 1: verify source URL
    try:
        verify_arxiv_source(args.source_url)
    except ValueError as exc:
        logger.error("Source verification failed: %s", exc)
        sys.exit(2)

    if args.local_test:
        logger.info("Running in local‑test mode – generating synthetic data.")
        df = generate_synthetic_subset()
        output_file = OUTPUT_DIR / SYNTHETIC_FILENAME
        _save_dataframe(df, output_file)
        sys.exit(0)

    # Real data download path
    output_file = OUTPUT_DIR / "cherrl_logs.csv"
    try:
        download_from_huggingface(output_path=output_file)
    except SystemExit as exc:
        # Propagate the non‑zero exit code for loud failure semantics.
        logger.error("Download failed with exit code %s", exc.code)
        sys.exit(exc.code)

if __name__ == "__main__":
    main()
