"""
Spatial Imputation Utility for Bird Migration Data.

This module provides functions to impute missing values in spatial data
using an inverse distance weighting (IDW) approach based on neighboring
observations within a specified radius.
"""

import logging
from typing import Optional, Union

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth (in degrees).

    Note: For small radii (< 10 degrees), Euclidean distance in lat/lon space
    is often sufficient and faster. However, to be precise with the 'radius'
    parameter in degrees, we use a simplified Euclidean approximation on the
    projected plane for small distances, or Haversine if strictly needed.
    Given the task specifies 'radius=1.0' (degrees), a Euclidean approximation
    on lat/lon is standard for local spatial interpolation in this context.
    """
    # Convert to radians
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of Earth in km
    return c * r


def impute_spatial_missing(
    df: pd.DataFrame,
    column: str,
    radius: float = 1.0
) -> pd.DataFrame:
    """
    Impute missing values in a specified column using inverse distance weighting (IDW)
    from neighboring points within a given radius (in degrees).

    For each missing value in `column`:
    1. Find neighbors within `radius` degrees (Euclidean distance in lat/lon space).
    2. Compute weighted average of neighbor values (weight = 1 / distance).
    3. Fill the missing value with the weighted average.
    4. Mark the row as imputed.

    If no neighbors are found within the radius, the value remains NaN.

    Args:
        df: Input DataFrame with columns including 'lat', 'lon', and the target `column`.
        column: The name of the column containing missing values to impute.
        radius: Maximum distance in degrees to consider as a neighbor.

    Returns:
        A new DataFrame with the imputed values and an additional boolean column
        `is_imputed` indicating which rows were imputed.

    Raises:
        ValueError: If required columns 'lat' or 'lon' are missing.
        KeyError: If the specified `column` does not exist.
    """
    if 'lat' not in df.columns or 'lon' not in df.columns:
        raise ValueError("DataFrame must contain 'lat' and 'lon' columns for spatial imputation.")

    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")

    # Create a copy to avoid modifying the original
    result_df = df.copy()
    result_df['is_imputed'] = False

    # Identify missing values
    missing_mask = result_df[column].isna()
    if not missing_mask.any():
        logger.info(f"No missing values found in column '{column}'.")
        return result_df

    # Prepare coordinates for KDTree (only non-missing rows for the target column)
    # We need coordinates of all points to find neighbors, but values only from non-missing
    coords = result_df[['lat', 'lon']].to_numpy()
    values = result_df[column].to_numpy()

    # Create KDTree for efficient neighbor search
    tree = cKDTree(coords)

    # Find indices of missing rows
    missing_indices = np.where(missing_mask)[0]

    imputed_count = 0

    for idx in missing_indices:
        lat, lon = coords[idx]
        # Query neighbors within radius (approximate Euclidean in degrees)
        # Note: cKDTree uses Euclidean distance. For 1 degree, this is acceptable
        # for local imputation as requested.
        neighbor_indices = tree.query_ball_point([lat, lon], r=radius)

        # Filter out the point itself and neighbors with missing values in the target column
        valid_neighbors = [
            i for i in neighbor_indices
            if i != idx and not np.isnan(values[i])
        ]

        if valid_neighbors:
            # Calculate distances and weights
            distances = []
            weights = []
            for n_idx in valid_neighbors:
                n_lat, n_lon = coords[n_idx]
                # Calculate Euclidean distance in degrees for weighting
                dist = np.sqrt((lat - n_lat)**2 + (lon - n_lon)**2)
                if dist > 0:
                    distances.append(dist)
                    weights.append(1.0 / dist)

            if distances:
                # Compute weighted average
                weights = np.array(weights)
                neighbor_values = np.array([values[i] for i in valid_neighbors])
                weighted_avg = np.sum(weights * neighbor_values) / np.sum(weights)

                result_df.loc[idx, column] = weighted_avg
                result_df.loc[idx, 'is_imputed'] = True
                imputed_count += 1
            else:
                # All neighbors were at the exact same location (dist=0) and valid
                # This is rare but possible if duplicates exist.
                # Fallback to simple average of neighbors at same location
                neighbor_values = np.array([values[i] for i in valid_neighbors])
                result_df.loc[idx, column] = np.mean(neighbor_values)
                result_df.loc[idx, 'is_imputed'] = True
                imputed_count += 1
        else:
            logger.debug(f"No valid neighbors found for row {idx} within radius {radius} degrees.")

    logger.info(f"Imputed {imputed_count} missing values in column '{column}'.")
    return result_df


def load_climate_data(path: str) -> pd.DataFrame:
    """
    Load climate data from a file (Parquet or CSV).
    This is a placeholder for the actual data loading logic used in the pipeline.
    """
    if path.endswith('.parquet'):
        return pd.read_parquet(path)
    elif path.endswith('.csv'):
        return pd.read_csv(path)
    else:
        raise ValueError("Unsupported file format. Use .parquet or .csv.")


def identify_missing_values(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Identify missing values in a specific column.
    """
    return df[column].isna()


def interpolate_spatial(df: pd.DataFrame, column: str, radius: float = 1.0) -> pd.DataFrame:
    """
    Wrapper for impute_spatial_missing to match legacy interface if needed.
    """
    return impute_spatial_missing(df, column, radius)


def save_imputed_data(df: pd.DataFrame, path: str) -> None:
    """
    Save the imputed DataFrame to a file.
    """
    if path.endswith('.parquet'):
        df.to_parquet(path, index=False)
    elif path.endswith('.csv'):
        df.to_csv(path, index=False)
    else:
        raise ValueError("Unsupported file format. Use .parquet or .csv.")


def run_imputation_pipeline(input_path: str, output_path: str, column: str, radius: float = 1.0) -> None:
    """
    Run the full imputation pipeline: load, impute, and save.
    """
    logger.info(f"Starting imputation pipeline for {input_path}")
    df = load_climate_data(input_path)
    df_imputed = impute_spatial_missing(df, column, radius)
    save_imputed_data(df_imputed, output_path)
    logger.info(f"Imputation pipeline completed. Output saved to {output_path}")


def main():
    """
    CLI entry point for the imputation utility.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Spatial Imputation Utility")
    parser.add_argument("input", help="Path to input data file (CSV or Parquet)")
    parser.add_argument("output", help="Path to output data file (CSV or Parquet)")
    parser.add_argument("--column", required=True, help="Column name to impute")
    parser.add_argument("--radius", type=float, default=1.0, help="Radius in degrees (default: 1.0)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    run_imputation_pipeline(args.input, args.output, args.column, args.radius)


if __name__ == "__main__":
    main()
