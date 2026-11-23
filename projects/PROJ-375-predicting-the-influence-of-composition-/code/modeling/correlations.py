"""
Correlation Analysis Module for Metallic Glass Thermal Expansion Study.

Implements Pearson correlation calculation between compositional features
and the target variable (CTE) on the test split.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.io import setup_logging

# Configure logging
logger = setup_logging(__name__)

# Constants
FEATURES = ["mean_atomic_radius", "electronegativity_var", "vec", "size_mismatch"]
TARGET = "cte"
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "test_split.parquet"
OUTPUT_PATH = PROJECT_ROOT / "results" / "correlations.csv"

def load_test_data() -> pd.DataFrame:
    """
    Load the test split from the processed parquet file.

    Returns:
        pd.DataFrame: The test dataset.

    Raises:
        FileNotFoundError: If the test split file does not exist.
        ValueError: If the file is empty or lacks required columns.
    """
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Test split file not found at {INPUT_PATH}. "
            "Ensure T022 (save_clean_data) and T018 (data splitting) have completed successfully."
        )

    try:
        df = pd.read_parquet(INPUT_PATH)
    except Exception as e:
        raise RuntimeError(f"Failed to load parquet file: {e}")

    if df.empty:
        raise ValueError("Test split DataFrame is empty. Cannot calculate correlations.")

    required_cols = FEATURES + [TARGET]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in test split: {missing}. "
            f"Expected: {required_cols}"
        )

    logger.info(f"Loaded test split: {len(df)} rows, {df.shape[1]} columns.")
    return df

def calculate_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Pearson correlation coefficient between each feature and CTE.

    Args:
        df: DataFrame containing features and target.

    Returns:
        pd.DataFrame: DataFrame with columns 'feature' and 'correlation_coefficient'.
    """
    results = []
    for feature in FEATURES:
        # Drop rows with NaN in either feature or target for this calculation
        valid_mask = df[feature].notna() & df[TARGET].notna()
        if valid_mask.sum() < 2:
            logger.warning(f"Not enough valid pairs for {feature} to calculate correlation.")
            corr_val = np.nan
        else:
            # Calculate Pearson correlation
            corr_val, _ = np.corrcoef(df.loc[valid_mask, feature], df.loc[valid_mask, TARGET])

        results.append({
            "feature": feature,
            "correlation_coefficient": round(float(corr_val), 4) if not np.isnan(corr_val) else np.nan
        })

    return pd.DataFrame(results)

def save_results(df: pd.DataFrame) -> None:
    """
    Save the correlation results to CSV.

    Args:
        df: DataFrame with correlation results.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved correlation results to {OUTPUT_PATH}")

def main() -> None:
    """
    Main entry point for the correlation analysis task.
    """
    logger.info("Starting Pearson correlation analysis (Task T038)...")

    try:
        # Load data
        test_data = load_test_data()

        # Calculate correlations
        corr_df = calculate_correlations(test_data)

        # Save results
        save_results(corr_df)

        logger.info("Task T038 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during correlation analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
