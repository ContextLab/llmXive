"""
Spatial interpolation of missing climate data.

This module implements spatial interpolation for missing climate data points
using scipy's griddata function with neighbor search in degrees (lat/lon).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

# Import config for logging setup
from src.config import setup_logging

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()

# Constants
MISSING_VALUE = np.nan
IMPUTED_FLAG_COLUMN = "is_imputed"
OUTPUT_FILE = "data/interim/climate_imputed.parquet"
METADATA_FILE = "data/interim/climate_imputed_metadata.json"


def load_climate_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load climate data from parquet file.

    Args:
        input_path: Path to climate parquet file. If None, uses default path.

    Returns:
        DataFrame with columns: lat, lon, temp, week, precip

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required columns are missing
    """
    if input_path is None:
        input_path = "data/raw/climate.parquet"

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Climate data file not found: {path}")

    logger.info(f"Loading climate data from {path}")
    df = pd.read_parquet(path)

    required_columns = ["lat", "lon", "temp", "week", "precip"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    logger.info(f"Loaded {len(df)} climate records")
    return df


def identify_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Identify missing values in temperature and precipitation columns.

    Args:
        df: DataFrame with climate data

    Returns:
        Tuple of (DataFrame with is_imputed flag, dict of missing counts)
    """
    df = df.copy()
    df[IMPUTED_FLAG_COLUMN] = False

    missing_counts = {}
    for col in ["temp", "precip"]:
        missing_count = df[col].isna().sum()
        missing_counts[col] = int(missing_count)
        logger.info(f"Missing values in {col}: {missing_count}")

    return df, missing_counts


def interpolate_spatial(
    df: pd.DataFrame,
    target_cols: Optional[list] = None,
    method: str = "linear",
    fill_value: float = MISSING_VALUE
) -> pd.DataFrame:
    """
    Perform spatial interpolation for missing climate values using griddata.

    Uses neighbor search in degrees (lat/lon) at an appropriate spatial scale.
    Only interpolates points where the target column is missing.

    Args:
        df: DataFrame with climate data (lat, lon, temp, week, precip)
        target_cols: Columns to interpolate. If None, uses ["temp", "precip"]
        method: Interpolation method for griddata ("linear", "nearest", "cubic")
        fill_value: Value to use for extrapolation (points outside convex hull)

    Returns:
        DataFrame with interpolated values and is_imputed flag
    """
    if target_cols is None:
        target_cols = ["temp", "precip"]

    df = df.copy()
    df[IMPUTED_FLAG_COLUMN] = False

    # Get coordinates
    lat = df["lat"].values
    lon = df["lon"].values
    points = np.column_stack([lat, lon])

    for col in target_cols:
        if col not in df.columns:
            logger.warning(f"Column {col} not found, skipping")
            continue

        # Identify missing values
        missing_mask = df[col].isna()
        missing_count = missing_mask.sum()

        if missing_count == 0:
            logger.info(f"No missing values in {col}, skipping interpolation")
            continue

        # Get known values
        known_mask = ~missing_mask
        if not known_mask.any():
            logger.warning(f"All values in {col} are missing, cannot interpolate")
            continue

        # Known points and values
        known_points = points[known_mask]
        known_values = df.loc[known_mask, col].values

        # Missing points
        missing_points = points[missing_mask]

        # Interpolate
        logger.info(f"Interpolating {missing_count} missing values in {col} using {method}")
        interpolated_values = griddata(
            known_points,
            known_values,
            missing_points,
            method=method,
            fill_value=fill_value
        )

        # Handle extrapolation (values outside convex hull)
        if fill_value != MISSING_VALUE:
            extrapolated = (interpolated_values == fill_value)
            if extrapolated.any():
                logger.warning(
                    f"{extrapolated.sum()} points in {col} are outside convex hull "
                    "and could not be interpolated"
                )
                # For points that couldn't be interpolated, keep as NaN
                interpolated_values[extrapolated] = MISSING_VALUE

        # Update DataFrame
        df.loc[missing_mask, col] = interpolated_values
        df.loc[missing_mask, IMPUTED_FLAG_COLUMN] = True

        logger.info(f"Interpolation complete for {col}: {missing_count} values processed")

    return df


def save_imputed_data(
    df: pd.DataFrame,
    missing_counts: Dict[str, int],
    output_path: Optional[str] = None,
    metadata_path: Optional[str] = None
) -> None:
    """
    Save imputed data and metadata.

    Args:
        df: DataFrame with imputed climate data
        missing_counts: Dictionary of original missing counts per column
        output_path: Path for output parquet file
        metadata_path: Path for metadata JSON file
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    if metadata_path is None:
        metadata_path = METADATA_FILE

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving imputed data to {output_file}")
    df.to_parquet(output_file, index=False)

    # Create metadata
    metadata = {
        "total_records": int(len(df)),
        "imputed_records": int(df[IMPUTED_FLAG_COLUMN].sum()),
        "original_missing_counts": missing_counts,
        "output_columns": list(df.columns),
        "imputation_method": "scipy.griddata with neighbor search in degrees"
    }

    metadata_file = Path(metadata_path)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved metadata to {metadata_file}")


def run_imputation_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    metadata_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the complete imputation pipeline.

    Args:
        input_path: Path to input climate parquet file
        output_path: Path for output parquet file
        metadata_path: Path for metadata JSON file

    Returns:
        DataFrame with imputed climate data
    """
    logger.info("Starting climate data imputation pipeline")

    # Load data
    df = load_climate_data(input_path)

    # Identify missing values
    df, missing_counts = identify_missing_values(df)

    # Check if there's anything to do
    total_missing = sum(missing_counts.values())
    if total_missing == 0:
        logger.info("No missing values found, no interpolation needed")
        df[IMPUTED_FLAG_COLUMN] = False
    else:
        # Perform spatial interpolation
        df = interpolate_spatial(df)

    # Save results
    save_imputed_data(df, missing_counts, output_path, metadata_path)

    logger.info("Imputation pipeline completed successfully")
    return df


def main():
    """Main entry point for the imputation pipeline."""
    logger.info("Running climate data imputation pipeline")
    try:
        run_imputation_pipeline()
        logger.info("Pipeline completed successfully")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
