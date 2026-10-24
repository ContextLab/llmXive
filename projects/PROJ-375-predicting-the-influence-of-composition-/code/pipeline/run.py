"""
Minimal pipeline runner for the quick‑start demonstration.

Usage:
    python -m pipeline.run --sample 100

The script reads the first N rows of the curated CSV, computes the required
compositional descriptors, adds a SHA‑256 checksum per row, writes the
enriched DataFrame to ``results/sample_output.parquet`` and validates the
output against the dataset JSON‑Schema contract.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

# Project‑specific utilities
from features.descriptors import extract_descriptors
from features.dataset_models import validate_dataframe_schema
from utils.io import compute_sha256

logger = get_logger(__name__)


def _load_raw_csv(csv_path: Path) -> pd.DataFrame:
    """Load the curated metallic‑glass CSV."""
    if not csv_path.is_file():
        logger.error(f"Raw CSV not found at {csv_path}")
        raise FileNotFoundError(f"Raw CSV not found at {csv_path}")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded raw CSV with {len(df)} rows from {csv_path}")
    return df


def _add_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the four required descriptors for each ``composition`` entry and
    attach them as new columns.
    """
    descriptor_rows = []
    for idx, row in df.iterrows():
        comp = row["composition"]
        try:
            desc = extract_descriptors(comp)
        except Exception as exc:
            logger.error(f"Descriptor extraction failed for row {idx} ({comp}): {exc}")
            raise
        descriptor_rows.append(desc)
    desc_df = pd.DataFrame(descriptor_rows)
    df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    return df


def _add_checksum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a SHA‑256 checksum of the JSON representation of each row (excluding
    the checksum column itself) and store it in a new ``checksum`` column.
    """
    checksums = []
    for _, row in df.iterrows():
        # Convert row to a dict without the checksum (it does not exist yet)
        row_dict = row.to_dict()
        # Ensure deterministic ordering
        json_repr = json.dumps(row_dict, sort_keys=True).encode("utf-8")
        checksums.append(compute_sha256(json_repr))
    df["checksum"] = checksums
    return df


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal pipeline on a sample of the curated dataset.")
    parser.add_argument(
        "--sample",
        type=int,
        default=100,
        help="Number of rows from the curated CSV to process (default: 100).",
    )
    args = parser.parse_args()

    # 1️⃣ Load raw data
    raw_csv_path = paths.data("raw", "curated_metallic_glass.csv")
    try:
        raw_df = _load_raw_csv(raw_csv_path)
    except Exception:
        logger.critical("Unable to load the curated CSV. Aborting.")
        return 1

    # 2️⃣ Take the first N rows
    sample_df = raw_df.head(args.sample).copy()
    logger.info(f"Selected first {len(sample_df)} rows for the quick‑start run.")

    # 3️⃣ Compute descriptors
    try:
        enriched_df = _add_descriptors(sample_df)
    except Exception:
        logger.critical("Descriptor computation failed.")
        return 1

    # 4️⃣ Add checksum column
    enriched_df = _add_checksum(enriched_df)

    # 5️⃣ Validate against the schema
    if not validate_dataframe_schema(enriched_df):
        logger.error("DataFrame does not conform to the mg_dataset schema.")
        return 1
    logger.info("Schema validation passed.")

    # 6️⃣ Write output parquet
    output_path = paths.results("sample_output.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_df.to_parquet(output_path, index=False)
    logger.info(f"Sample output written to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
