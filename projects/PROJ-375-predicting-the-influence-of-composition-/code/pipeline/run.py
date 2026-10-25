"""
Minimal pipeline runner for the quick‑start demonstration.

Usage:
    python -m pipeline.run --sample 100

The script reads the first N rows of the curated CSV, computes the required
compositional descriptors, ensures schema compliance for both original and
quick-start contracts, adds a SHA‑256 checksum per row, writes the
enriched DataFrame to ``results/sample_output.parquet`` and validates the
output against the dataset JSON‑Schema contract.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
import requests

from llmxive_toolkit import paths, get_logger

# Project‑specific utilities
from features.descriptors import extract_descriptors
from features.dataset_models import validate_dataframe_schema
from utils.io import compute_sha256, setup_logging

logger = get_logger(__name__)

# URL of a publicly hosted curated metallic‑glass dataset (real data)
CURATED_DATA_URL = (
    "https://raw.githubusercontent.com/Materials-Data-Science-and-Informatics/"
    "metallic_glass_dataset/master/data/metallic_glass_cte.csv"
)

def _download_curated_csv(dest_path: Path) -> None:
    """Download the curated CSV from the verified remote location."""
    logger.info(f"Downloading curated dataset from {CURATED_DATA_URL}")
    response = requests.get(CURATED_DATA_URL, timeout=30)
    response.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(response.content)
    logger.info(f"Saved curated CSV to {dest_path}")

def _load_raw_csv(csv_path: Path) -> pd.DataFrame:
    """Load the curated metallic‑glass CSV, downloading it if missing."""
    if not csv_path.is_file():
        logger.warning(f"Raw CSV not found at {csv_path}. Attempting download.")
        try:
            _download_curated_csv(csv_path)
        except Exception as exc:
            logger.error(f"Failed to download curated CSV: {exc}")
            raise FileNotFoundError(
                f"Unable to obtain curated CSV at {csv_path}"
            ) from exc
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded raw CSV with {len(df)} rows from {csv_path}")

    # Normalise column names (case‑insensitive) to the expected lower‑case names
    df.columns = [col.strip().lower() for col in df.columns]
    return df

def _add_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the four required descriptors for each ``composition`` entry.
    Uses the public API from features.descriptors to ensure schema compliance.
    """
    descriptor_rows = []
    for idx, row in df.iterrows():
        comp = row["composition"]
        try:
            # extract_descriptors returns a dict with keys:
            # weighted_mean_atomic_radius, electronegativity_variance, vec, atomic_size_coefficient_of_variation
            desc = extract_descriptors(comp)
            descriptor_rows.append(desc)
        except Exception as exc:
            logger.error(f"Descriptor extraction failed for row {idx} ({comp}): {exc}")
            raise

    desc_df = pd.DataFrame(descriptor_rows)
    # Reset index to ensure concatenation aligns perfectly
    df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    return df

def _ensure_schema_compliance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the DataFrame contains all columns required by validate_dataframe_schema,
    including both the 'Original' and 'Quick-start' schema sets.
    """
    # Map Quick-start descriptors to Original schema names
    df["mean_atomic_radius"] = df["weighted_mean_atomic_radius"]
    df["electronegativity_var"] = df["electronegativity_variance"]
    df["size_mismatch"] = df["atomic_size_coefficient_of_variation"]
    # 'vec' is already named 'vec' in both schemas.
    
    # Add amorphous_flag (default to True for this curated sample of metallic glasses)
    df["amorphous_flag"] = True
    
    return df

def _add_checksum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a SHA‑256 checksum of the JSON representation of each row.
    """
    checksums = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        # sort_keys=True is critical for deterministic hashing
        json_repr = json.dumps(row_dict, sort_keys=True).encode("utf-8")
        checksums.append(compute_sha256(json_repr))
    df["checksum"] = checksums
    return df

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a minimal pipeline on a sample of the curated dataset."
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=100,
        help="Number of rows from the curated CSV to process (default: 100).",
    )
    args = parser.parse_args()

    setup_logging()

    # 1️⃣ Load raw data
    raw_csv_path = paths.data("raw", "curated_metallic_glass.csv")
    try:
        raw_df = _load_raw_csv(raw_csv_path)
    except Exception as exc:
        logger.critical(f"Unable to load the curated CSV: {exc}")
        return 1

    # Verify required columns exist
    required_columns = {"composition", "cte"}
    if not required_columns.issubset(set(raw_df.columns)):
        missing = required_columns - set(raw_df.columns)
        logger.error(f"Input CSV is missing required columns: {missing}")
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

    # 4️⃣ Ensure schema compliance (map columns for original schema)
    enriched_df = _ensure_schema_compliance(enriched_df)

    # 5️⃣ Add checksum column
    enriched_df = _add_checksum(enriched_df)

    # 6️⃣ Validate against the schema
    if not validate_dataframe_schema(enriched_df):
        logger.error("DataFrame does not conform to the expected schema.")
        return 1
    logger.info("Schema validation passed.")

    # 7️⃣ Write output parquet
    output_path = paths.results("sample_output.parquet")
    enriched_df.to_parquet(output_path, index=False)
    logger.info(f"Sample output written to {output_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
