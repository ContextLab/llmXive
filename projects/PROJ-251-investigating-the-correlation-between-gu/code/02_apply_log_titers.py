"""
Task T021: Log-Transform Titers & LOD Handling.

Reads the merged dataset from T020c (cleared_with_diversity.csv),
applies LOD imputation (0.5 * LOD_VALUE) to titer values below detection
(or 'ND'/'0' if applicable), and computes log-transformed titers.
Writes the updated dataset back to data/processed/cleared_with_diversity.csv.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_lod_value, get_use_synthetic_data, ensure_directories
from utils.logging_config import get_logger, log_exclusion_count

logger = get_logger(__name__)


def load_cleared_data() -> pd.DataFrame:
    """Load the dataset produced by T020c."""
    input_path = project_root / "data" / "processed" / "cleared_with_diversity.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T020c (Shannon Diversity) has completed."
        )
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def apply_lod_imputation_and_log_transform(
    df: pd.DataFrame,
    lod_value: float
) -> pd.DataFrame:
    """
    Apply LOD imputation and log-transform to titer columns.

    Steps:
    1. Ensure titer columns are numeric.
    2. Impute 'ND', '0', or NaN values with 0.5 * lod_value.
    3. Compute log10(titer) for baseline and post-vaccination.
    """
    df = df.copy()

    titer_cols = ["titer_baseline", "titer_post"]
    missing_cols = [c for c in titer_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required titer columns: {missing_cols}. "
            "Ensure T011d (Merge) has completed successfully."
        )

    # Ensure numeric, coercing errors to NaN
    for col in titer_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Identify values to impute: NaN, 0, or string 'ND' (if not already coerced)
    impute_value = 0.5 * lod_value
    logger.info(f"Imputing values below LOD ({lod_value}) with {impute_value}")

    # Replace 0 and NaN with impute_value
    # Note: If 'ND' was a string that survived to_numeric, it's now NaN.
    for col in titer_cols:
        null_mask = df[col].isna()
        zero_mask = (df[col] == 0)
        mask_to_impute = null_mask | zero_mask
        count = mask_to_impute.sum()
        if count > 0:
            logger.warning(
                f"Imputing {count} {col} values (0 or NaN) with {impute_value}"
            )
            df.loc[mask_to_impute, col] = impute_value

    # Compute log-transformed titers (log10)
    # Since we imputed 0s and NAs, all values should be > 0 now
    log_cols = ["titer_pre_log", "titer_post_log"]
    for orig_col, log_col in zip(titer_cols, log_cols):
        df[log_col] = np.log10(df[orig_col])

    logger.info("Log-transform applied successfully.")
    return df


def write_updated_dataset(df: pd.DataFrame) -> None:
    """Write the updated dataset back to the processed directory."""
    output_path = project_root / "data" / "processed" / "cleared_with_diversity.csv"
    ensure_directories()
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote updated dataset to {output_path} with {len(df)} rows")


def run_log_titer_pipeline() -> None:
    """Main pipeline execution for T021."""
    ensure_directories()

    lod_value = get_lod_value()
    if lod_value is None:
        logger.warning(
            "LOD_VALUE not set in config. Defaulting to 10.0 as per spec edge cases."
        )
        lod_value = 10.0

    logger.info(f"Starting T021: Log-Transform Titers (LOD={lod_value})")

    df = load_cleared_data()
    df_transformed = apply_lod_imputation_and_log_transform(df, lod_value)
    write_updated_dataset(df_transformed)

    logger.info("T021 completed successfully.")


def main() -> None:
    run_log_titer_pipeline()


if __name__ == "__main__":
    main()