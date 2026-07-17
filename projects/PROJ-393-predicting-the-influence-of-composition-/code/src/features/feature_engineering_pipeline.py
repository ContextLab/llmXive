"""
Feature Engineering Pipeline for Heusler Alloy Hysteresis Prediction.

This module orchestrates the application of compositional descriptors to the
preprocessed alloy dataset and saves the enriched dataset with features.

Dependencies:
  - code/src/features/descriptor_calculator.py (calculate_all_descriptors)
  - data/processed/alloys_raw.csv (Input from T027)
  - data/processed/alloys_features.csv (Output)
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Import from sibling module using the verified API surface
from src.features.descriptor_calculator import calculate_all_descriptors
from src.utils.logging_config import setup_logging

# Configure logger
logger = setup_logging(__name__)


def load_processed_data(input_path: Path) -> pd.DataFrame:
    """
    Load the preprocessed alloys dataset.

    Args:
        input_path: Path to 'data/processed/alloys_raw.csv'

    Returns:
        DataFrame containing the raw processed alloy data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_csv(input_path)

    if df.empty:
        raise ValueError(f"Input file {input_path} is empty. Cannot compute features.")

    required_cols = ["composition", "coercivity_Oe", "saturation_magnetization_emu_g"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def apply_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply descriptor calculation to every row in the DataFrame.

    This function calls `calculate_all_descriptors` for each row,
    extracting the composition string and returning the full row with
    appended feature columns.

    Args:
        df: DataFrame with at least a 'composition' column.

    Returns:
        DataFrame with original columns plus new descriptor columns:
        - avg_electronegativity
        - valence_electron_concentration
        - atomic_radii_variance
        - avg_d_electrons
        - atomic_size_mismatch
    """
    logger.info("Starting feature engineering on all rows...")

    # Use apply to process row by row
    # The descriptor_calculator expects a dict-like row with 'composition'
    def process_row(row):
        try:
            descriptors = calculate_all_descriptors(row)
            # Merge original row with descriptors
            return pd.Series({**row, **descriptors})
        except Exception as e:
            logger.error(f"Error processing row with composition '{row.get('composition', 'N/A')}': {e}")
            # Return original row with NaNs for descriptors to avoid dropping data
            result = pd.Series(row)
            result["avg_electronegativity"] = None
            result["valence_electron_concentration"] = None
            result["atomic_radii_variance"] = None
            result["avg_d_electrons"] = None
            result["atomic_size_mismatch"] = None
            return result

    # Apply function
    df_features = df.apply(process_row, axis=1)

    logger.info(f"Feature engineering complete. Calculated {len(df_features.columns) - len(df.columns)} new features.")
    return df_features


def save_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the feature-enriched DataFrame to CSV.

    Args:
        df: DataFrame with added features.
        output_path: Destination path (e.g., 'data/processed/alloys_features.csv').
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved feature-enriched dataset to {output_path} ({len(df)} rows)")


def run_feature_engineering_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main orchestration function for the feature engineering pipeline.

    Steps:
      1. Load raw processed data (default: data/processed/alloys_raw.csv).
      2. Calculate descriptors for all rows.
      3. Save results (default: data/processed/alloys_features.csv).

    Args:
        input_path: Optional override for input file path.
        output_path: Optional override for output file path.

    Returns:
        The resulting DataFrame with features.
    """
    if input_path is None:
        input_path = Path("data/processed/alloys_raw.csv")
    if output_path is None:
        output_path = Path("data/processed/alloys_features.csv")

    logger.info(f"Feature Engineering Pipeline starting.")
    logger.info(f"Input: {input_path}, Output: {output_path}")

    df_raw = load_processed_data(input_path)
    df_features = apply_descriptors(df_raw)
    save_features(df_features, output_path)

    logger.info("Feature Engineering Pipeline completed successfully.")
    return df_features


def main() -> None:
    """Entry point for script execution."""
    run_feature_engineering_pipeline()


if __name__ == "__main__":
    main()
