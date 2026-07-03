"""
Spatial interpolation module for missing climate data.

This module implements spatial interpolation of missing climate data using
scipy.interpolate.griddata with a 1° radius neighbor search in degrees.
"""

import logging
import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

# Configure logger
logger = logging.getLogger(__name__)


def load_climate_data(input_path: str) -> pd.DataFrame:
    """
    Load climate data from parquet file.

    Args:
        input_path: Path to the input parquet file.

    Returns:
        DataFrame with columns: lat, lon, temp, week, precip.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_parquet(input_path)
    required_cols = {"lat", "lon", "temp", "week", "precip"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    return df


def interpolate_missing_values(
    df: pd.DataFrame,
    radius_deg: float = 1.0,
    method: str = "linear"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform spatial interpolation for missing climate values.

    Uses scipy.interpolate.griddata with a 1° radius neighbor search.

    Args:
        df: Input DataFrame with lat, lon, temp, week, precip columns.
        radius_deg: Radius in degrees for neighbor search (default 1.0).
        method: Interpolation method ('linear', 'nearest', 'cubic').

    Returns:
        Tuple of (imputed_df, flag_df):
            - imputed_df: DataFrame with missing values filled.
            - flag_df: DataFrame with boolean flags indicating imputed cells.
    """
    # Create a copy to avoid modifying original
    imputed_df = df.copy()

    # Track which cells were imputed
    imputed_flags = pd.DataFrame(
        {"temp_imputed": False, "precip_imputed": False},
        index=df.index
    )

    # Group by week to perform interpolation within each time period
    weeks = df["week"].unique()
    logger.info(f"Processing {len(weeks)} weeks for spatial interpolation")

    for week in weeks:
        week_mask = df["week"] == week
        week_data = df[week_mask].copy()

        # Identify rows with missing temp or precip
        missing_temp = week_data["temp"].isna()
        missing_precip = week_data["precip"].isna()

        if not (missing_temp.any() or missing_precip.any()):
            continue

        # Get available (non-missing) data for this week
        valid_mask = week_data["temp"].notna() & week_data["precip"].notna()
        valid_data = week_data[valid_mask]

        if len(valid_data) < 3:
            logger.warning(
                f"Week {week}: Insufficient valid data points ({len(valid_data)}) "
                "for interpolation. Skipping."
            )
            continue

        # Extract coordinates and values
        source_coords = valid_data[["lat", "lon"]].values
        source_temp = valid_data["temp"].values
        source_precip = valid_data["precip"].values

        # Build KDTree for efficient neighbor search
        tree = cKDTree(source_coords)

        # Process missing temp values
        if missing_temp.any():
            missing_indices = week_data[missing_temp].index
            missing_coords = week_data.loc[missing_indices, ["lat", "lon"]].values

            # Find neighbors within radius
            distances, neighbor_indices = tree.query(
                missing_coords, k=len(valid_data), distance_upper_bound=radius_deg
            )

            # Handle case where no neighbors found (query returns inf)
            has_neighbors = np.isfinite(distances).any(axis=1)

            if not has_neighbors.any():
                logger.warning(
                    f"Week {week}: No neighbors found for any missing temp values."
                )
                continue

            # For each missing point, use available neighbors for interpolation
            for i, idx in enumerate(missing_indices):
                if not has_neighbors[i]:
                    continue

                # Get valid neighbors for this point
                point_neighbors = neighbor_indices[i][np.isfinite(distances[i])]
                point_distances = distances[i][np.isfinite(distances[i])]

                if len(point_neighbors) == 0:
                    continue

                # Use griddata with available neighbors
                query_point = missing_coords[i:i+1]
                neighbor_coords = source_coords[point_neighbors]
                neighbor_temp = source_temp[point_neighbors]

                try:
                    interpolated_val = griddata(
                        neighbor_coords,
                        neighbor_temp,
                        query_point,
                        method=method
                    )
                    if not np.isnan(interpolated_val[0]):
                        imputed_df.loc[idx, "temp"] = interpolated_val[0]
                        imputed_flags.loc[idx, "temp_imputed"] = True
                except Exception as e:
                    logger.warning(
                        f"Week {week}, point {idx}: Interpolation failed for temp: {e}"
                    )

        # Process missing precip values (similar logic)
        if missing_precip.any():
            missing_indices = week_data[missing_precip].index
            missing_coords = week_data.loc[missing_indices, ["lat", "lon"]].values

            distances, neighbor_indices = tree.query(
                missing_coords, k=len(valid_data), distance_upper_bound=radius_deg
            )

            has_neighbors = np.isfinite(distances).any(axis=1)

            if not has_neighbors.any():
                logger.warning(
                    f"Week {week}: No neighbors found for any missing precip values."
                )
                continue

            for i, idx in enumerate(missing_indices):
                if not has_neighbors[i]:
                    continue

                point_neighbors = neighbor_indices[i][np.isfinite(distances[i])]
                point_distances = distances[i][np.isfinite(distances[i])]

                if len(point_neighbors) == 0:
                    continue

                query_point = missing_coords[i:i+1]
                neighbor_coords = source_coords[point_neighbors]
                neighbor_precip = source_precip[point_neighbors]

                try:
                    interpolated_val = griddata(
                        neighbor_coords,
                        neighbor_precip,
                        query_point,
                        method=method
                    )
                    if not np.isnan(interpolated_val[0]):
                        imputed_df.loc[idx, "precip"] = interpolated_val[0]
                        imputed_flags.loc[idx, "precip_imputed"] = True
                except Exception as e:
                    logger.warning(
                        f"Week {week}, point {idx}: Interpolation failed for precip: {e}"
                    )

    return imputed_df, imputed_flags


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """Main entry point for climate data imputation."""
    # Paths
    input_path = "data/raw/climate.parquet"
    output_path = "data/interim/climate_imputed.parquet"
    flag_path = "data/interim/climate_imputation_flags.parquet"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info(f"Loading climate data from {input_path}")

    try:
        df = load_climate_data(input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except ValueError as e:
        logger.error(str(e))
        raise

    logger.info(f"Loaded {len(df)} records. Missing temp: {df['temp'].isna().sum()}, "
               f"Missing precip: {df['precip'].isna().sum()}")

    if df["temp"].isna().sum() == 0 and df["precip"].isna().sum() == 0:
        logger.info("No missing values found. Copying input to output.")
        df.to_parquet(output_path, index=False)
        # Create empty flags file
        pd.DataFrame(index=df.index).to_parquet(flag_path, index=False)
        return

    logger.info("Starting spatial interpolation...")
    imputed_df, flag_df = interpolate_missing_values(df)

    # Log summary
    temp_imputed = flag_df["temp_imputed"].sum()
    precip_imputed = flag_df["precip_imputed"].sum()
    logger.info(f"Imputed {temp_imputed} temperature values and "
               f"{precip_imputed} precipitation values.")

    # Check for remaining missing values
    remaining_temp = imputed_df["temp"].isna().sum()
    remaining_precip = imputed_df["precip"].isna().sum()

    if remaining_temp > 0 or remaining_precip > 0:
        logger.warning(
            f"Warning: {remaining_temp} temperature and "
            f"{remaining_precip} precipitation values could not be imputed."
        )

    # Write outputs
    logger.info(f"Writing imputed data to {output_path}")
    imputed_df.to_parquet(output_path, index=False)

    logger.info(f"Writing imputation flags to {flag_path}")
    flag_df.to_parquet(flag_path, index=False)

    # Compute and log checksums
    output_hash = compute_file_hash(output_path)
    flag_hash = compute_file_hash(flag_path)
    logger.info(f"Output file hash: {output_hash}")
    logger.info(f"Flags file hash: {flag_hash}")

    logger.info("Imputation complete.")


if __name__ == "__main__":
    main()
