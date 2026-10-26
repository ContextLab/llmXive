import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd

# Project logger
from utils.logging_config import get_logger

logger = get_logger(__name__)

def calculate_detection_rate(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Calculate the detection rate for each protein (column).

    Returns a DataFrame with detection rates.
    """
    detection_rates = (df.notna().sum() / len(df)) >= threshold
    return detection_rates

def filter_low_abundance_proteins(
    df: pd.DataFrame,
    min_detection_rate: float = 0.5
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out proteins with low detection rates.

    Returns:
        Tuple of (filtered DataFrame, list of dropped column names).
    """
    logger.info(f"Filtering proteins with detection rate < {min_detection_rate}")
    detection_mask = calculate_detection_rate(df, min_detection_rate)
    kept_cols = detection_mask[detection_mask].index.tolist()
    dropped_cols = [col for col in df.columns if col not in kept_cols]

    if dropped_cols:
        logger.info(f"Dropped {len(dropped_cols)} low‑abundance protein columns: {dropped_cols}")
    else:
        logger.info("No low‑abundance protein columns were dropped.")

    filtered_df = df[kept_cols]
    return filtered_df, dropped_cols

def apply_lcm_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Left‑Censored Missing (LCM) imputation using MinProb algorithm.

    This implementation attempts to use 'imp3' if available, otherwise
    falls back to a custom MinProb implementation.
    """
    logger.info("Applying LCM (MinProb) imputation to missing values.")
    try:
        from imp3 import impute_minprob
        imputed = impute_minprob(df.values)
        imputed_df = pd.DataFrame(imputed, index=df.index, columns=df.columns)
        logger.info("Imputation completed using imp3 library.")
        return imputed_df
    except ImportError:
        logger.warning("imp3 library not available; using custom MinProb implementation.")
        # Simple custom min‑prob imputation: replace NA with half of the minimum non‑NA value per column
        imputed_df = df.copy()
        for col in imputed_df.columns:
            col_vals = imputed_df[col]
            min_val = col_vals.min(skipna=True)
            if pd.isna(min_val):
                logger.warning(f"Column {col} contains only NA values; leaving as NA.")
                continue
            fill_val = min_val / 2.0
            imputed_df[col] = col_vals.fillna(fill_val)
        logger.info("Custom MinProb imputation completed.")
        return imputed_df

def log_deviation(method: str, reason: str):
    """
    Log a deviation from the standard protocol to the deviation log.
    """
    logger.warning(f"Deviation from standard protocol: {method} – {reason}")

def run_normalization_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    min_detection_rate: float = 0.5
) -> Tuple[pd.DataFrame, dict]:
    """
    Run the full normalization pipeline: filter low abundance + LCM imputation.
    """
    logger.info("Starting normalization pipeline...")

    if input_path is None:
        processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"
        possible_files = [
            processed_dir / "merged.csv",
            processed_dir / "merged_matrix.csv",
            processed_dir / "processed_data.csv"
        ]
        for f in possible_files:
            if f.exists():
                input_path = f
                break
        if input_path is None:
            raise FileNotFoundError("No input CSV found for normalization.")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path, index_col=0)

    # Filter low‑abundance proteins
    filtered_df, dropped_cols = filter_low_abundance_proteins(df, min_detection_rate)

    # Impute missing values
    imputed_df = apply_lcm_imputation(filtered_df)

    # Determine output path
    if output_path is None:
        output_path = Path(__file__).resolve().parents[3] / "data" / "processed" / "normalized_matrix.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    imputed_df.to_csv(output_path)
    logger.info(f"Normalization pipeline completed. Normalized data saved to {output_path}")

    stats = {
        "dropped_columns": dropped_cols,
        "rows": imputed_df.shape[0],
        "columns": imputed_df.shape[1]
    }
    return imputed_df, stats

def main():
    """
    CLI entry point.
    """
    try:
        run_normalization_pipeline()
    except Exception as e:
        logger.error(f"Normalization pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
